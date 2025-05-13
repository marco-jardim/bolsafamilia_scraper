import os
import re
import sys
import time
import csv
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
URL_PRINCIPAL = (
    "https://portaldatransparencia.gov.br/beneficios/beneficiario/consulta"
    "?ordenarPor=nomeBeneficiario&direcao=asc"
)
URL_BASE = "https://portaldatransparencia.gov.br/beneficios/beneficiario/consulta/resultado"

TAMANHO_PAGINA = 20000
DIRECAO_ORDENACAO = "asc"
COLUNA_ORDENACAO = "nomeBeneficiario"
UF = "RJ"
ANOS = range(2019, 2025)

DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

COLUNAS_SELECIONADAS = (
    "linkDetalhamento,"
    "uf,"
    "nomeBeneficiario,"
    "linguagemCidada,"
    "nisBeneficio,"
    "cpfBeneficiario,"
    "municipio,"
    "ano,"
    "valor"
)

# Interval (seconds) between consecutive GET requests
REQUEST_INTERVAL = 1

# Interval (seconds) after which we re-fetch cookies (challenge renew)
CHALLENGE_RENEW_INTERVAL = 60

# How many times to retry the same offset if we get an error
MAX_ATTEMPTS = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/110.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def parse_valor(valor_str: str) -> float:
    """
    Converte strings como "2.250,00", " - 978,67" etc. em float (ex: 2250.00, -978.67).
    Se não for possível converter, retorna 0.0 e loga um aviso.
    """
    if not valor_str:
        return 0.0
    valor_str = valor_str.strip().replace(" - ", "-").replace("- ", "-")
    valor_str = valor_str.replace(".", "").replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        print(f"Valor inválido para conversão: '{valor_str}'. Usando 0.0.")
        return 0.0

def extract_id_municipio(link: str) -> str:
    """Captura 'municipio=12345' e retorna '12345'."""
    if not link:
        return ""
    match = re.search(r"municipio=(\d+)", link)
    return match.group(1) if match else ""

def open_browser_and_get_cookies():
    """
    Abre Chrome via undetected-chromedriver, visita a página principal
    para resolver o desafio WAF, aguarda ~15s e pega cookies.
    Retorna uma list[dict] de cookies.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
    # Se quiser headless, descomente:
    # chrome_options.add_argument("--headless")

    driver = uc.Chrome(options=chrome_options)

    print("[Desafio] Abrindo o navegador para obter cookies...")
    driver.get(URL_PRINCIPAL)
    time.sleep(15)  # Ajuste se necessário para o WAF challenge

    cookies = driver.get_cookies()
    # Fecha explicitamente e remove a referência:
    driver.quit()
    driver = None

    return cookies

def inject_cookies(sess: requests.Session, cookie_list):
    """
    Injeta os cookies (list of dict, do Selenium) na Session do requests.
    """
    for c in cookie_list:
        domain = c.get("domain", "portaldatransparencia.gov.br")
        sess.cookies.set(name=c['name'], value=c['value'], domain=domain)

def baixar_dados_ano(session: requests.Session, ano: int, last_challenge_time: float):
    """
    Faz as requisições paginadas usando a 'session'.
    Retorna (session, last_challenge_time) ao final.
    """
    offset = 0
    csv_filename = os.path.join(DOWNLOADS_FOLDER, f"bolsafamilia_{ano}_{UF}.csv")

    csv_columns = [
        "uf", "municipio", "ano", "valor",
        "skBeneficiario", "nomeBeneficiario",
        "nisBeneficio", "cpfBeneficiario",
        "linguagemCidada", "idMunicipio",
    ]

    with open(csv_filename, mode="w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns, delimiter=";")
        writer.writeheader()

        while True:
            # Check if it's time to re-challenge
            now = time.time()
            if (now - last_challenge_time) >= CHALLENGE_RENEW_INTERVAL:
                print("[Renew] 1 minuto passou. Renovando cookies...")
                new_cookies = open_browser_and_get_cookies()
                session = requests.Session()
                inject_cookies(session, new_cookies)
                last_challenge_time = time.time()

            print(f"[{ano}] Requisição com offset={offset}")

            attempts = 0
            while attempts < MAX_ATTEMPTS:
                try:
                    params = {
                        "paginacaoSimples": "true",
                        "tamanhoPagina": TAMANHO_PAGINA,
                        "offset": offset,
                        "direcaoOrdenacao": DIRECAO_ORDENACAO,
                        "colunaOrdenacao": COLUNA_ORDENACAO,
                        "ano": ano,
                        "uf": UF,
                        "colunasSelecionadas": COLUNAS_SELECIONADAS,
                    }

                    resp = session.get(URL_BASE, params=params, headers=HEADERS, timeout=30)
                    code = resp.status_code

                    if code == 403:
                        print("HTTP 403 - Bloqueado. Renovando cookies e tentando novamente.")
                        new_cookies = open_browser_and_get_cookies()
                        session = requests.Session()
                        inject_cookies(session, new_cookies)
                        last_challenge_time = time.time()
                        attempts += 1
                        time.sleep(5)
                        continue
                    elif code == 202:
                        print("HTTP 202 (Accepted) - Aguardando 5s e tentando de novo...")
                        attempts += 1
                        time.sleep(5)
                        continue
                    elif code != 200:
                        print(f"HTTP {code} - Encerrando loop para ano {ano}.")
                        return session, last_challenge_time

                    data_json = resp.json()
                    if data_json.get("error") is not None:
                        print(f"Erro retornado pela API: {data_json['error']}")
                        return session, last_challenge_time

                    registros = data_json.get("data", [])
                    if not registros:
                        print(f"Nenhum registro encontrado (offset={offset}). Encerrando ano {ano}.")
                        return session, last_challenge_time

                    # Se chegou aqui, parseamos com sucesso
                    for item in registros:
                        link = item.get("linkDetalhamento", "")
                        id_municipio = extract_id_municipio(link)
                        valor_float = parse_valor(item.get("valor", ""))

                        row = {
                            "uf": item.get("uf"),
                            "municipio": item.get("municipio"),
                            "ano": item.get("ano"),
                            "valor": valor_float,
                            "skBeneficiario": item.get("skBeneficiario"),
                            "nomeBeneficiario": item.get("nomeBeneficiario"),
                            "nisBeneficio": item.get("nisBeneficio"),
                            "cpfBeneficiario": item.get("cpfBeneficiario"),
                            "linguagemCidada": item.get("linguagemCidada"),
                            "idMunicipio": id_municipio,
                        }
                        writer.writerow(row)

                    # Se deu tudo certo, break do attempts loop
                    break

                except Exception as e:
                    attempts += 1
                    print(f"Erro inesperado no offset={offset}, tentativa {attempts}/{MAX_ATTEMPTS}: {e}")
                    # Re-challenge
                    new_cookies = open_browser_and_get_cookies()
                    session = requests.Session()
                    inject_cookies(session, new_cookies)
                    last_challenge_time = time.time()
                    time.sleep(5)

            if attempts >= MAX_ATTEMPTS:
                print(f"Falhou {MAX_ATTEMPTS} vezes no offset={offset}. Encerrando ano {ano}.")
                return session, last_challenge_time

            # Offset concluído, vamos para o próximo
            offset += TAMANHO_PAGINA
            time.sleep(REQUEST_INTERVAL)

    print(f"Finalizado ano {ano}. CSV: {csv_filename}")
    return session, last_challenge_time


def main():
    # 1) Primeira vez: abre browser para pegar cookies
    cookies = open_browser_and_get_cookies()

    # 2) Cria session e injeta cookies
    session = requests.Session()
    inject_cookies(session, cookies)

    last_challenge_time = time.time()

    # 3) Itera anos
    for ano in ANOS:
        session, last_challenge_time = baixar_dados_ano(session, ano, last_challenge_time)

    print("Processo concluído.")
    # Força encerramento total do script
    sys.exit(0)


if __name__ == "__main__":
    main()

# Script de Extração de Dados de Benefícios (Portal da Transparência)

Este projeto contém um script em Python que faz **download de dados** do Portal da Transparência, filtrando por um estado específico (por padrão, `RJ`) e por uma faixa de anos (2019 a 2024).
Para cada ano, salva em um arquivo CSV local, **convertendo** campos (por exemplo, o `valor`) e **extraindo** algumas informações adicionais (como o `idMunicipio`).

## Sumário

- [Script de Extração de Dados de Benefícios (Portal da Transparência)](#script-de-extração-de-dados-de-benefícios-portal-da-transparência)
  - [Sumário](#sumário)
  - [Pré-requisitos](#pré-requisitos)
    - [Observação sobre `distutils`](#observação-sobre-distutils)
  - [Instalação](#instalação)
  - [Como executar](#como-executar)
  - [O que o script faz](#o-que-o-script-faz)
  - [Estrutura dos arquivos CSV](#estrutura-dos-arquivos-csv)
  - [Erros comuns](#erros-comuns)
  - [Estratégias de proteção anti-bot (Cloudflare) e soluções adotadas](#estratégias-de-proteção-anti-bot-cloudflare-e-soluções-adotadas)

---

## Pré-requisitos

1. **Python 3.7+** instalado (recomendado Python 3.9 ou superior).
2. As seguintes **bibliotecas**:

   * `requests` (para requisições HTTP)
   * `undetected-chromedriver` e `selenium` (para simular um navegador e contornar proteção anti-bot)
   * `csv`, `re`, `time`, etc. (já inclusas na biblioteca padrão do Python, exceto `time` e `re` que são nativas)
   * Além de outras que podem estar listadas no `requirements.txt`.

### Observação sobre `distutils`

Em algumas versões mais recentes do Python, o módulo `distutils` não está mais incluído por padrão, o que pode gerar erros ao instalar `undetected-chromedriver`. Se isso ocorrer, tente:

```bash
pip install --upgrade setuptools wheel
```

ou instalar `python3-distutils` via gerenciador de pacotes (em Linux).

---

## Instalação

1. **Clonar** este repositório (ou baixar os arquivos).
2. **Entrar** na pasta do projeto via terminal:

   ```bash
   cd bolsafamilia_scraper
   ```
3. **Criar** (opcional, mas recomendado) um **ambiente virtual** no Python:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate no Windows
   ```
4. **Instalar** as dependências necessárias:

   ```bash
   pip install -r requirements.txt
   ```

Caso não possua o arquivo `requirements.txt`, instale manualmente (exemplo):

```bash
pip install requests selenium undetected-chromedriver
```

---

## Como executar

No terminal, dentro da pasta do projeto (com o ambiente virtual ativado se estiver usando), rode:

```bash
python baixar_beneficios.py
```

Onde `baixar_beneficios.py` é o nome do script principal. Ajuste caso seu arquivo tenha outro nome.

---

## O que o script faz

1. **Baixa dados paginados** de um endpoint do Portal da Transparência (benefícios sociais).
2. **Filtra** por um estado definido no código (por padrão, `RJ`).
3. **Itera** sobre uma faixa de anos (padrão 2019 até 2024).
4. Para cada ano, **cria (ou sobrescreve)** um arquivo CSV na pasta `downloads/`, contendo os registros daquele ano. O nome do arquivo segue o padrão:

   ```
   bolsafamilia_<ANO>_<UF>.csv
   ```

   Exemplos: `bolsafamilia_2019_RJ.csv`, `bolsafamilia_2020_RJ.csv` etc.
5. **Converte** o campo `valor` (por exemplo, `"2.250,00"`) para um número decimal (`2250.00`).
6. **Extrai** do campo `linkDetalhamento` o `idMunicipio` (via expressão regular) e inclui no CSV (no campo `idMunicipio`).
7. **Omite** campos como `filtros` e `linkDetalhamento` no CSV final, ficando apenas com colunas definidas no script.

Durante o processo, o script:

* Usa **Selenium** com **`undetected-chromedriver`** para visitar a página principal e obter **cookies** (necessários para contornar o WAF/Cloudflare).
* **Renova** esses cookies periodicamente (a cada 1 minuto, por exemplo) para não ser bloqueado.
* Faz um **loop** paginado (`offset += 20000` por padrão), salvando cada lote de registros.

---

## Estrutura dos arquivos CSV

Cada arquivo CSV contém colunas como:

* `uf` (ex.: `"RJ"`)
* `municipio` (ex.: `"DUQUE DE CAXIAS"`)
* `ano` (ex.: `2025`)
* `valor` (float, ex.: `1800.0`)
* `skBeneficiario` (ex.: `18410691`)
* `nomeBeneficiario` (ex.: `"ACARMELUCIA DA SILVA ROCHA"`)
* `nisBeneficio` (ex.: `"2.383.451.058-7"`)
* `cpfBeneficiario` (ex.: `"***.247.707-**"`)
* `linguagemCidada` (ex.: `"Novo Bolsa Família"`)
* `idMunicipio` (extraído do `linkDetalhamento`, ex.: `"21835"`)

Cada linha corresponde a um beneficiário/registro retornado pela API do Portal da Transparência.

---

## Erros comuns

1. **`ModuleNotFoundError: No module named 'distutils'`**

   * Tente atualizar `setuptools` e `wheel`:

     ```bash
     pip install --upgrade setuptools wheel
     ```
   * Em alguns Linux, instale via pacote `python3-distutils`.

2. **HTTP 202, 403, 405, 429** ao fazer requisições

   * Indica **bloqueio ou limitação** do servidor (Cloudflare/WAF). O script tenta contornar renovando cookies e dormindo entre requisições. Ajuste intervalos se persistir.

3. **`ReadTimeout` / `ConnectionError`**

   * Ocorre quando o servidor demora ou a conexão falha. O script faz até **3 tentativas** (`MAX_ATTEMPTS`), reabrindo cookies no Chrome se preciso.

4. **“OSError: \[WinError 6] Identificador inválido”** ao encerrar

   * Uma mensagem inofensiva que às vezes aparece na finalização do `undetected-chromedriver` no Windows. Geralmente não impede o funcionamento.

5. **CSV vazio** (só cabeçalho)

   * Pode acontecer se não houver dados para aquele ano ou se ocorreu bloqueio inicial. Verifique se a API realmente possui dados para o período e se não houve erro de cookies.

---

## Estratégias de proteção anti-bot (Cloudflare) e soluções adotadas

O Portal da Transparência (assim como muitos sites) utiliza **Cloudflare** ou outro WAF que:

* Injeta **JavaScript** para validar se o cliente é um navegador real.
* Pode **limitar** requisições (HTTP 202, 403, 429 etc.) para tráfegos suspeitos.

Para **superar** isso, o script:

1. **Selenium + undetected-chromedriver**

   * Abre um Chrome real (em modo automatizado), executa o JS do WAF e pega cookies válidos.
   * Assim, o servidor vê um “navegador” de verdade, liberando o acesso.

2. **Renovação de cookies**

   * A cada 60 segundos (valor ajustável), reabre o navegador e gera novos cookies.
   * Evita que a mesma sessão seja bloqueada se fizer muitas requisições.

3. **Intervalos e tentativas**

   * A cada página, o script **aguarda** (por padrão, `REQUEST_INTERVAL = 1` segundo ou mais) para não parecer um bot muito rápido.
   * Se receber 202 ou 403, **tenta novamente** até `MAX_ATTEMPTS`, reabrindo cookies caso necessário.

4. **Retry com re-challenge**

   * Em caso de exceções de rede (timeout) ou bloqueios, faz nova obtenção de cookies com `undetected-chromedriver` e **repete** a requisição do mesmo `offset`.

Estas estratégias reduzem a chance de bloqueio, mas não garantem 100% — se o portal tiver um limite muito estrito, pode ainda ocorrer. Nesse caso, aumentar ainda mais pausas, reduzir `TAMANHO_PAGINA` ou agendar extrações em horários diferentes.

---

**Fim**. Com essas informações, você pode:

* **Instalar** e executar o script.
* Entender como ele **baixa** dados e **armazena** em CSV.
* Ajustar a **tolerância** a bloqueios (intervalos, número de tentativas, etc.).
* Mitigar problemas de rate limit e WAF anti-bot.

Bom uso!

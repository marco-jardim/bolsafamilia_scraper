# Script de Extração de Dados de Benefícios (Portal da Transparência)

Este projeto contém um script em Python que faz download de dados do Portal da Transparência, filtrando por um estado específico e por uma faixa de anos.
Para cada ano, salva em um arquivo CSV local, convertendo campos e extraindo algumas informações adicionais.

## Sumário

- [Script de Extração de Dados de Benefícios (Portal da Transparência)](#script-de-extração-de-dados-de-benefícios-portal-da-transparência)
  - [Sumário](#sumário)
  - [Pré-requisitos](#pré-requisitos)
  - [Instalação](#instalação)
  - [Como executar](#como-executar)
  - [O que o script faz](#o-que-o-script-faz)
  - [Estrutura dos arquivos CSV](#estrutura-dos-arquivos-csv)
  - [Observações](#observações)

---

## Pré-requisitos

1. **Python 3.7+** instalado (preferencialmente use uma versão atualizada, como 3.9 ou superior).
2. **Bibliotecas** necessárias listadas em `requirements.txt` (ou mencionadas abaixo).

Em linhas gerais, o script utiliza:

* `requests` para fazer as requisições HTTP.
* `csv` (biblioteca nativa do Python) para escrever arquivos CSV.
* `re` (expressões regulares, também nativa).

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

---

## Como executar

No terminal, dentro da pasta do projeto (e com o ambiente virtual ativado se estiver usando), rode:

```bash
python baixar_beneficios.py
```

Onde `baixar_beneficios.py` é o nome do script principal (ajuste caso você tenha outro nome de arquivo).

---

## O que o script faz

1. **Baixa dados paginados** do Portal da Transparência, consultando um endpoint de benefícios sociais.
2. **Filtra** por um estado definido no código (ex.: `RJ`).
3. **Itera** sobre uma faixa de anos (no exemplo, 2019 até 2024).
4. Para cada ano, **cria (ou sobrescreve)** um arquivo CSV, contendo os registros daquele ano. O nome do arquivo segue o padrão:

   ```
   bolsafamilia_<ANO>_<UF>.csv
   ```

   Exemplo: `bolsafamilia_2019_RJ.csv`, `bolsafamilia_2020_RJ.csv`, etc.
5. **Converte** o campo `valor` (por exemplo, `"2.250,00"`) para um número decimal (`2250.00`) armazenado como `float`.
6. **Extrai** do campo `linkDetalhamento` o `idMunicipio` (via expressão regular) e inclui este dado no CSV (no campo `idMunicipio`).
7. **Omite** os campos `filtros` e `linkDetalhamento` no CSV final, salvando apenas as colunas definidas no script.

---

## Estrutura dos arquivos CSV

Cada arquivo CSV contém as colunas:

* `uf` (ex.: `"RJ"`)
* `municipio` (ex.: `"DUQUE DE CAXIAS"`)
* `ano` (ex.: `2025`)
* `valor` (**float**; ex.: `1800.0`)
* `skBeneficiario` (ex.: `18410691`)
* `nomeBeneficiario` (ex.: `"ACARMELUCIA DA SILVA ROCHA"`)
* `nisBeneficio` (ex.: `"2.383.451.058-7"`)
* `cpfBeneficiario` (ex.: `"***.247.707-**"`)
* `linguagemCidada` (ex.: `"Novo Bolsa Família"`)
* `idMunicipio` (campo extraído da URL; ex.: `"21835"`)

Cada linha corresponde a um beneficiário/registro retornado pela API do Portal da Transparência.

## Observações

- O script pode demorar um pouco para rodar, dependendo da quantidade de dados retornados pela API.
- O download dos dados é feito de forma paginada, ou seja, o script vai buscar os dados em várias páginas (caso existam).
- Os arquivos CSV são sobrescritos a cada execução do script. Se você quiser manter os dados de anos anteriores, faça um backup dos arquivos antes de rodar o script novamente.
- Os arquivos CSV são salvos na pasta `downloads`, que é criada automaticamente pelo script se não existir.

# PDF to HTML AI Ingestion

## Sobre o Projeto
Uma aplicacao web desenvolvida com Streamlit para converter documentos PDF (especialmente manuais e relatorios) em arquivos HTML estruturados. O objetivo principal deste conversor e preparar documentos para serem consumidos por modelos de Inteligencia Artificial (LLMs).

A ferramenta resolve o problema de perda de contexto visual em PDFs extraindo o conteudo de forma sequencial (preservando a ordem de leitura) e embutindo as imagens capturadas diretamente no corpo do HTML utilizando codificacao Base64. Isso permite que agentes de IA processem o texto e as telas de sistemas na exata ordem em que aparecem no documento original, em um unico payload.

## Funcionalidades
* Interface web amigavel para usuarios nao-tecnicos.
* Leitura sequencial de blocos de PDF (texto e imagem).
* Conversao e embutimento automatico de imagens para Base64.
* Filtro de ruido para ignorar imagens menores que 1KB (icones de formatacao).
* Preservacao de negrito e hierarquia de paragrafos.
* Geracao de arquivo HTML pronto para download e injecao em prompts.

## Tecnologias Utilizadas
* Python 3
* Streamlit (Interface Web)
* PyMuPDF (Motor de extracao e processamento de PDF)

## Como Executar Localmente

1. Clone este repositorio:
```bash
git clone [https://github.com/AntonioLelis/PDFtoHTML.git](https://github.com/AntonioLelis/PDFtoHTML.git)
cd PDFtoHTML
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv

# No Windows:
.venv\Scripts\activate

# No Linux/Mac:
source .venv/bin/activate
```

3. Instale as dependencias:
```bash
pip install -r requirements.txt
```
*(Nota: O pacote correto para manipulacao do PDF e PyMuPDF, nao fitz)*

4. Execute a aplicacao:
```bash
streamlit run app.py
```

5. Acesse no seu navegador atraves do endereco http://localhost:8501.

## Estrutura do Codigo
A logica central utiliza o metodo `get_text("dict")` do PyMuPDF para mapear os elementos da pagina. Blocos do tipo 0 sao processados como texto (com extracao de metadados de fonte para formatacao basica), enquanto blocos do tipo 1 sao processados como imagem, convertidos para bytes e codificados para compor a tag `<img>` do HTML final.
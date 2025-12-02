# Especificação canônica de campos de licitação

Este documento consolida os campos mínimos para representação estruturada de editais e pregões, seus tipos/formatos e exemplos de payload válidos e inválidos para validação automatizada.

## 1. Lista canônica de campos

| Campo              | Descrição                                                                 | Tipo / Formato                                           | Obrigatório | Enum / Restrições principais                              |
| ------------------ | ------------------------------------------------------------------------- | -------------------------------------------------------- | ----------- | --------------------------------------------------------- |
| `objeto`           | Descrição objetiva do objeto da contratação                               | string (min. 10 caracteres)                              | Sim         | Sem enum; remover espaços extras                          |
| `orgao`            | Órgão ou entidade responsável                                             | string (min. 3 caracteres)                               | Sim         | Sem enum                                                  |
| `modalidade`       | Modalidade da licitação                                                   | enum                                                     | Sim         | `concorrencia`, `pregao_eletronico`, `pregao_presencial`, `tomada_precos`, `concurso`, `registro_preco`, `dispensa`, `inexigibilidade` |
| `tipo_julgamento`  | Critério de julgamento das propostas                                      | enum                                                     | Sim         | `menor_preco`, `maior_desconto`, `maior_lance`, `melhor_tecnica`, `tecnica_e_preco`, `maior_oferta` |
| `prazos`           | Marcos temporais relevantes                                                | objeto                                                   | Sim         | Datas em ISO 8601; tempos em dias/horas                   |
| `habilitacao`      | Requisitos de habilitação exigidos                                        | objeto                                                   | Sim         | Boleanos para eixos padrão; lista livre em `outros`       |
| `anexos`           | Relação de anexos ou arquivos complementares                              | array de objetos                                         | Não         | `url` como URL válida; `nome` min. 3 caracteres           |
| `penalidades`      | Penalidades previstas                                                     | array de objetos                                         | Não         | `tipo` e `fundamento_legal` min. 3 caracteres             |

## 2. JSON Schema e modelos Pydantic

Os modelos foram implementados em [`schemas/campos_canonicos.py`](../schemas/campos_canonicos.py) usando Pydantic v2. O schema completo pode ser obtido via `LicitacaoCanonica.model_json_schema()`, enquanto os schemas individuais de cada campo são expostos pela função `campo_json_schemas()`.

```python
from schemas.campos_canonicos import LicitacaoCanonica, campo_json_schemas

# JSON Schema completo
payload_schema = LicitacaoCanonica.model_json_schema()

# Schemas por campo (já com $ref resolvido)
campo_schemas = campo_json_schemas()
```

Principais validações implementadas:

- **Strings**: uso de `constr` com `strip_whitespace=True` para normalizar entradas e garantir tamanho mínimo.
- **Enums**: modalidades e tipos de julgamento protegidos contra valores fora da lista permitida.
- **Datas/horas**: campos como `data_abertura` usam `datetime` e exigem formato ISO 8601 na serialização JSON.
- **Prazos numéricos**: `validade_proposta_dias` e demais prazos usam inteiros positivos ou não-negativos conforme aplicável.
- **Listas**: `anexos` e `penalidades` permitem múltiplos itens, mantendo coerência com o schema raiz.

## 3. Exemplos para validação automatizada

### Exemplo válido

```json
{
  "objeto": "Aquisição de computadores para laboratórios educacionais",
  "orgao": "Secretaria Municipal de Educação",
  "modalidade": "pregao_eletronico",
  "tipo_julgamento": "menor_preco",
  "prazos": {
    "data_abertura": "2024-07-15T10:00:00-03:00",
    "data_limite_esclarecimentos": "2024-07-10T18:00:00-03:00",
    "data_limite_impugnacao": "2024-07-08T18:00:00-03:00",
    "validade_proposta_dias": 60,
    "prazo_execucao_dias": 30,
    "prazo_entrega_documentos_horas": 24
  },
  "habilitacao": {
    "regularidade_fiscal": true,
    "capacidade_tecnica": true,
    "qualif_economica": true,
    "declaracao_me_epp": false,
    "visitas_tecnicas": false,
    "outros": ["Certificação ISO 9001", "Registro no CREA"]
  },
  "anexos": [
    {
      "nome": "Termo de Referência",
      "url": "https://exemplo.gov.br/arquivos/tr.pdf",
      "obrigatorio": true
    }
  ],
  "penalidades": [
    {
      "tipo": "multa_atraso",
      "fundamento_legal": "Art. 86, Lei 8.666/93",
      "descricao": "Aplicável após 5 dias corridos de atraso na entrega"
    }
  ]
}
```

### Exemplo inválido (motivos comentados)

```json
{
  "objeto": "Compra",
  "orgao": "",
  "modalidade": "chamada_publica",
  "tipo_julgamento": "menor_preco",
  "prazos": {
    "data_abertura": "15/07/2024 10h",
    "validade_proposta_dias": 0
  },
  "habilitacao": {
    "regularidade_fiscal": true,
    "capacidade_tecnica": true,
    "qualif_economica": true
  },
  "anexos": [
    {
      "nome": "TR",
      "url": "ftp://arquivos.local/tr.pdf"
    }
  ],
  "penalidades": [
    {
      "tipo": "",
      "fundamento_legal": "Art. 86, Lei 8.666/93"
    }
  ]
}
```

Erros esperados no exemplo inválido:

1. `objeto` com menos de 10 caracteres.
2. `orgao` vazio.
3. `modalidade` fora do enum aceito.
4. `data_abertura` fora do formato ISO 8601.
5. `validade_proposta_dias` deve ser inteiro positivo (> 0).
6. `anexos[0].url` não é HTTP/HTTPS válido.
7. `penalidades[0].tipo` não pode ser vazio (min. 3 caracteres).

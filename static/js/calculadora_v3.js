/**
 * Calculadora V3 - Universal
 * Suporta qualquer tipo de serviço com despesas personalizáveis
 */

// Variáveis globais
let dadosPasso1 = {};
let lotes = [];
let despesasPersonalizadas = [];
let parametros = {
    inss_patronal: 20.0,
    salario_educacao: 2.5,
    rat_sat: 3.0,
    fap_multiplicador: 1.0,
    sesc_senac: 1.5,
    sebrae: 0.6,
    incra: 0.2,
    regime_tributario: 'simples',
    aliquota_simples: 14.0,
    aliquota_pis: 0.65,
    aliquota_cofins: 3.0,
    aliquota_iss: 5.0,
    custos_indiretos_percentual: 5.0,
    lucro_percentual: 8.0
};

// Categorias de despesas disponíveis
const CATEGORIAS_DESPESAS = {
    'mao_obra': 'Mão de Obra Adicional',
    'material': 'Materiais',
    'equipamento': 'Equipamentos',
    'veiculo': 'Veículos',
    'operacional': 'Despesas Operacionais',
    'administrativa': 'Despesas Administrativas',
    'bdi': 'BDI/Despesas Indiretas',
    'outra': 'Outras Despesas'
};

// ============================================================
// INICIALIZAÇÃO
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    renderizarLotes();
});

function inicializarEventos() {
    // Slider de lucro com recálculo automático
    const sliderLucro = document.getElementById('lucro_percentual');
    if (sliderLucro) {
        sliderLucro.addEventListener('input', function() {
            document.getElementById('lucro_valor').textContent = this.value + '%';
            parametros.lucro_percentual = parseFloat(this.value);
            atualizarResumoCompleto();
        });
    }
    
    // Outros parâmetros
    const camposParametros = [
        'custos_indiretos', 'regime_tributario', 'aliquota_simples',
        'aliquota_pis', 'aliquota_cofins', 'aliquota_iss'
    ];
    
    camposParametros.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.addEventListener('change', function() {
                coletarParametros();
                atualizarResumoCompleto();
            });
        }
    });
    
    // Botão adicionar despesa
    const btnAdicionarDespesa = document.getElementById('adicionarDespesa');
    if (btnAdicionarDespesa) {
        btnAdicionarDespesa.addEventListener('click', adicionarDespesa);
    }
}

// ============================================================
// DESPESAS PERSONALIZÁVEIS
// ============================================================

function adicionarDespesa() {
    const despesa = {
        id: Date.now(),
        categoria: 'material',
        descricao: '',
        unidade: 'un',
        quantidade: 1,
        valor_unitario: 0,
        lote_numero: 1
    };
    
    despesasPersonalizadas.push(despesa);
    renderizarDespesas();
    atualizarResumoCompleto();
}

function renderizarDespesas() {
    const container = document.getElementById('despesasContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    despesasPersonalizadas.forEach((despesa, index) => {
        const html = `
            <div class="card mb-2 border-info">
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-md-2">
                            <label class="form-label">Categoria</label>
                            <select class="form-select" onchange="atualizarDespesa(${index}, 'categoria', this.value)">
                                ${Object.entries(CATEGORIAS_DESPESAS).map(([key, label]) => 
                                    `<option value="${key}" ${despesa.categoria === key ? 'selected' : ''}>${label}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Descrição</label>
                            <input type="text" class="form-control" value="${despesa.descricao || ''}"
                                   onchange="atualizarDespesa(${index}, 'descricao', this.value)">
                        </div>
                        <div class="col-md-1">
                            <label class="form-label">Unidade</label>
                            <input type="text" class="form-control" value="${despesa.unidade}"
                                   onchange="atualizarDespesa(${index}, 'unidade', this.value)">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Quantidade</label>
                            <input type="number" class="form-control" value="${despesa.quantidade}" step="0.01"
                                   onchange="atualizarDespesa(${index}, 'quantidade', parseFloat(this.value))">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Valor Unit. (R$)</label>
                            <input type="number" class="form-control" value="${despesa.valor_unitario}" step="0.01"
                                   onchange="atualizarDespesa(${index}, 'valor_unitario', parseFloat(this.value))">
                        </div>
                        <div class="col-md-1">
                            <label class="form-label">Lote</label>
                            <input type="number" class="form-control" value="${despesa.lote_numero}" min="1"
                                   onchange="atualizarDespesa(${index}, 'lote_numero', parseInt(this.value))">
                        </div>
                        <div class="col-md-1 d-flex align-items-end">
                            <button type="button" class="btn btn-danger w-100" onclick="removerDespesa(${index})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="mt-2">
                        <strong>Total:</strong> R$ ${formatarMoeda(despesa.quantidade * despesa.valor_unitario)}
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML += html;
    });
}

function atualizarDespesa(index, campo, valor) {
    despesasPersonalizadas[index][campo] = valor;
    renderizarDespesas();
    atualizarResumoCompleto();
}

function removerDespesa(index) {
    despesasPersonalizadas.splice(index, 1);
    renderizarDespesas();
    atualizarResumoCompleto();
}

// ============================================================
// RESUMO E CÁLCULO
// ============================================================

function atualizarResumoCompleto() {
    // Coletar todos os postos
    const todosPostos = [];
    const todosInsumos = [];
    
    lotes.forEach(lote => {
        lote.postos.forEach(posto => {
            todosPostos.push({
                ...posto,
                lote_numero: lote.numero,
                lote_nome: lote.nome
            });
        });
        
        lote.insumos.forEach(insumo => {
            todosInsumos.push({
                ...insumo,
                lote_numero: lote.numero
            });
        });
    });
    
    if (todosPostos.length === 0 && despesasPersonalizadas.length === 0) {
        return;
    }
    
    coletarParametros();
    
    // Chamar API de preview
    fetch('/precificaja/servicos/nova-lei/api/preview-v3', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            postos: todosPostos,
            insumos: todosInsumos,
            despesas: despesasPersonalizadas,
            parametros: parametros
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            atualizarResumoUI(data.resultado);
        }
    })
    .catch(error => {
        console.error('Erro ao atualizar resumo:', error);
    });
}

function atualizarResumoUI(resultado) {
    // Mão de obra
    document.getElementById('resumoRemuneracao').textContent = formatarMoeda(resultado.mao_obra.remuneracao);
    document.getElementById('resumoEncargos').textContent = formatarMoeda(resultado.mao_obra.encargos);
    document.getElementById('resumoProvisoes').textContent = formatarMoeda(resultado.mao_obra.provisoes);
    document.getElementById('resumoReposicao').textContent = formatarMoeda(resultado.mao_obra.reposicao);
    document.getElementById('resumoInsumos').textContent = formatarMoeda(resultado.mao_obra.insumos);
    
    // Despesas personalizadas
    document.getElementById('resumoDespesas').textContent = formatarMoeda(resultado.despesas_personalizadas.total);
    
    // Subtotal
    document.getElementById('resumoSubtotal').textContent = formatarMoeda(resultado.subtotal_antes_bdi);
    
    // BDI/CITL
    document.getElementById('resumoCustosIndiretos').textContent = formatarMoeda(resultado.bdi_citl.custos_indiretos);
    document.getElementById('resumoTributos').textContent = formatarMoeda(resultado.bdi_citl.tributos_total);
    document.getElementById('resumoLucro').textContent = formatarMoeda(resultado.bdi_citl.lucro);
    
    // Total
    document.getElementById('resumoPrecoTotal').textContent = formatarMoeda(resultado.total_geral);
    
    // Margem de lucro
    const margemLucro = (resultado.bdi_citl.lucro / resultado.total_geral * 100).toFixed(2);
    document.getElementById('resumoMargemLucro').textContent = margemLucro + '%';
}

function coletarParametros() {
    parametros = {
        inss_patronal: parseFloat(document.getElementById('inss_patronal')?.value || 20.0),
        salario_educacao: parseFloat(document.getElementById('salario_educacao')?.value || 2.5),
        rat_sat: parseFloat(document.getElementById('rat_sat')?.value || 3.0),
        fap_multiplicador: parseFloat(document.getElementById('fap')?.value || 1.0),
        sesc_senac: parseFloat(document.getElementById('sesc_senac')?.value || 1.5),
        sebrae: parseFloat(document.getElementById('sebrae')?.value || 0.6),
        incra: parseFloat(document.getElementById('incra')?.value || 0.2),
        regime_tributario: document.getElementById('regime_tributario')?.value || 'simples',
        aliquota_simples: parseFloat(document.getElementById('aliquota_simples')?.value || 14.0),
        aliquota_pis: parseFloat(document.getElementById('aliquota_pis')?.value || 0.65),
        aliquota_cofins: parseFloat(document.getElementById('aliquota_cofins')?.value || 3.0),
        aliquota_iss: parseFloat(document.getElementById('aliquota_iss')?.value || 5.0),
        custos_indiretos_percentual: parseFloat(document.getElementById('custos_indiretos')?.value || 5.0),
        lucro_percentual: parseFloat(document.getElementById('lucro_percentual')?.value || 8.0)
    };
}

// ============================================================
// LOTES E POSTOS (mantido da versão anterior)
// ============================================================

function renderizarLotes() {
    if (lotes.length === 0) {
        lotes.push({
            numero: 1,
            nome: 'Lote 1',
            postos: [],
            insumos: []
        });
    }
    
    // Implementação completa na versão anterior
}

// ============================================================
// UTILITÁRIOS
// ============================================================

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor || 0);
}

function mostrarToast(mensagem, tipo = 'success') {
    // Implementação de toast
    console.log(`[${tipo.toUpperCase()}] ${mensagem}`);
}

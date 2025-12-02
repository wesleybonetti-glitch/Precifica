/**
 * Calculadora Nova Lei - JavaScript
 * Gerencia o wizard de 2 passos e integração com API
 */

// ============================================================
// VARIÁVEIS GLOBAIS
// ============================================================

let dadosPasso1 = {};
let lotes = [];
let loteAtual = 1;
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

// ============================================================
// INICIALIZAÇÃO
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    verificarRecuperacaoSessao();
    atualizarCamposTributos();
});

function inicializarEventos() {
    // Passo 1
    const btnConsultarCNPJ = document.getElementById('consultarCNPJ');
    if (btnConsultarCNPJ) {
        btnConsultarCNPJ.addEventListener('click', consultarCNPJ);
    }
    
    const btnSalvarPasso1 = document.getElementById('salvarPasso1');
    if (btnSalvarPasso1) {
        btnSalvarPasso1.addEventListener('click', salvarPasso1);
    }
    
    // Passo 2
    const btnAdicionarLote = document.getElementById('adicionarLote');
    if (btnAdicionarLote) {
        btnAdicionarLote.addEventListener('click', adicionarLote);
    }
    
    const btnFinalizar = document.getElementById('finalizarPrecificacao');
    if (btnFinalizar) {
        btnFinalizar.addEventListener('click', finalizarPrecificacao);
    }
    
    // Parâmetros - atualizar resumo quando mudar
    const camposParametros = [
        'inss_patronal', 'salario_educacao', 'rat_sat', 'fap',
        'sesc_senac', 'sebrae', 'incra', 'regime_tributario',
        'aliquota_pis', 'aliquota_cofins', 'aliquota_iss',
        'aliquota_simples', 'custos_indiretos', 'lucro_percentual'
    ];
    
    camposParametros.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.addEventListener('change', function() {
                coletarParametros();
                atualizarResumo();
            });
        }
    });
    
    // Regime tributário
    const regimeTributario = document.getElementById('regime_tributario');
    if (regimeTributario) {
        regimeTributario.addEventListener('change', atualizarCamposTributos);
    }
}

// ============================================================
// PASSO 1: DADOS DA EMPRESA E ÓRGÃO
// ============================================================

function consultarCNPJ() {
    const cnpjInput = document.getElementById('cnpj');
    const cnpj = cnpjInput.value.replace(/\D/g, '');
    
    if (cnpj.length !== 14) {
        alert('CNPJ inválido! Digite 14 dígitos.');
        return;
    }
    
    // Mostrar loading
    const btn = document.getElementById('consultarCNPJ');
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Consultando...';
    btn.disabled = true;
    
    // Consultar API via backend (evita CORS)
    fetch(`/precificaja/servicos/nova-lei/api/consultar-cnpj/${cnpj}`)
        .then(response => response.json())
        .then(data => {
            if (!data.sucesso) {
                alert(data.erro || 'CNPJ não encontrado!');
                return;
            }
            
            // Preencher campos
            const dados = data.dados;
            document.getElementById('razao_social').value = dados.razao_social || '';
            document.getElementById('endereco').value = dados.endereco || '';
            
            mostrarToast('CNPJ consultado com sucesso!', 'success');
        })
        .catch(error => {
            console.error('Erro ao consultar CNPJ:', error);
            alert('Erro ao consultar CNPJ. Verifique sua conexão e tente novamente.');
        })
        .finally(() => {
            btn.innerHTML = textoOriginal;
            btn.disabled = false;
        });
}

function salvarPasso1() {
    const form = document.getElementById('formPasso1');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Coletar dados do formulário
    dadosPasso1 = {
        cnpj: document.getElementById('cnpj').value,
        razao_social: document.getElementById('razao_social').value,
        endereco: document.getElementById('endereco').value,
        numero_processo: document.getElementById('numero_processo').value,
        validade_proposta: parseInt(document.getElementById('validade_proposta').value),
        prazo_pagamento: document.getElementById('prazo_pagamento').value,
        local_execucao: document.getElementById('local_execucao').value,
        prazo_execucao: parseInt(document.getElementById('prazo_execucao').value),
        tipo_servico: document.getElementById('tipo_servico').value
    };
    
    // Salvar no localStorage
    salvarSessao();
    
    // Avançar para passo 2
    document.getElementById('passo1').style.display = 'none';
    document.getElementById('passo2').style.display = 'block';
    
    // Scroll para o topo
    window.scrollTo(0, 0);
    
    mostrarToast('Dados salvos! Agora adicione os lotes e postos.', 'success');
}

// ============================================================
// PASSO 2: LOTES E POSTOS
// ============================================================

function adicionarLote() {
    loteAtual++;
    
    const lote = {
        numero: loteAtual,
        nome: `Lote ${loteAtual}`,
        postos: [],
        insumos: []
    };
    
    lotes.push(lote);
    
    renderizarLotes();
    salvarSessao();
}

function renderizarLotes() {
    const container = document.getElementById('lotesContainer');
    
    if (lotes.length === 0) {
        // Adicionar lote inicial
        lotes.push({
            numero: 1,
            nome: 'Lote 1',
            postos: [],
            insumos: []
        });
    }
    
    container.innerHTML = '';
    
    lotes.forEach((lote, index) => {
        const loteHTML = criarLoteHTML(lote, index);
        container.innerHTML += loteHTML;
    });
    
    // Reativar event listeners
    ativarEventListenersLotes();
}

function criarLoteHTML(lote, index) {
    return `
        <div class="card mt-3" id="lote-${index}">
            <div class="card-header bg-primary text-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h4 class="mb-0">
                        <i class="fas fa-layer-group"></i>
                        ${lote.nome}
                    </h4>
                    <button type="button" class="btn btn-sm btn-danger" onclick="removerLote(${index})">
                        <i class="fas fa-trash"></i> Remover Lote
                    </button>
                </div>
            </div>
            <div class="card-body">
                <!-- Postos -->
                <h5 class="text-primary">
                    <i class="fas fa-users"></i>
                    Postos de Trabalho
                </h5>
                
                <div id="postos-lote-${index}">
                    ${lote.postos.map((posto, pIndex) => criarPostoHTML(posto, index, pIndex)).join('')}
                </div>
                
                <button type="button" class="btn btn-success mt-2" onclick="adicionarPosto(${index})">
                    <i class="fas fa-plus"></i> Adicionar Posto
                </button>
                
                <!-- Insumos -->
                <h5 class="text-primary mt-4">
                    <i class="fas fa-box"></i>
                    Insumos (Uniformes, EPIs, Materiais)
                </h5>
                
                <div id="insumos-lote-${index}">
                    ${lote.insumos.map((insumo, iIndex) => criarInsumoHTML(insumo, index, iIndex)).join('')}
                </div>
                
                <button type="button" class="btn btn-warning mt-2" onclick="adicionarInsumo(${index})">
                    <i class="fas fa-plus"></i> Adicionar Insumo
                </button>
            </div>
        </div>
    `;
}

function criarPostoHTML(posto, loteIndex, postoIndex) {
    return `
        <div class="card mb-2 border-success">
            <div class="card-body">
                <div class="row g-2">
                    <div class="col-md-3">
                        <label class="form-label">Cargo</label>
                        <input type="text" class="form-control" value="${posto.cargo || ''}" 
                               onchange="atualizarPosto(${loteIndex}, ${postoIndex}, 'cargo', this.value)">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Quantidade</label>
                        <input type="number" class="form-control" value="${posto.quantidade_postos || 1}" min="1"
                               onchange="atualizarPosto(${loteIndex}, ${postoIndex}, 'quantidade_postos', parseInt(this.value))">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Jornada</label>
                        <select class="form-select" onchange="atualizarPosto(${loteIndex}, ${postoIndex}, 'jornada_tipo', this.value)">
                            <option value="44h" ${posto.jornada_tipo === '44h' ? 'selected' : ''}>44h</option>
                            <option value="40h" ${posto.jornada_tipo === '40h' ? 'selected' : ''}>40h</option>
                            <option value="12x36_diurno" ${posto.jornada_tipo === '12x36_diurno' ? 'selected' : ''}>12x36 Diurno</option>
                            <option value="12x36_noturno" ${posto.jornada_tipo === '12x36_noturno' ? 'selected' : ''}>12x36 Noturno</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Salário Base (R$)</label>
                        <input type="number" class="form-control" value="${posto.salario_base || 0}" step="0.01"
                               onchange="atualizarPosto(${loteIndex}, ${postoIndex}, 'salario_base', parseFloat(this.value))">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Insalubridade (R$)</label>
                        <input type="number" class="form-control" value="${posto.adicional_insalubridade || 0}" step="0.01"
                               onchange="atualizarPosto(${loteIndex}, ${postoIndex}, 'adicional_insalubridade', parseFloat(this.value))">
                    </div>
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="button" class="btn btn-danger w-100" onclick="removerPosto(${loteIndex}, ${postoIndex})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function criarInsumoHTML(insumo, loteIndex, insumoIndex) {
    return `
        <div class="card mb-2 border-warning">
            <div class="card-body">
                <div class="row g-2">
                    <div class="col-md-2">
                        <label class="form-label">Tipo</label>
                        <select class="form-select" onchange="atualizarInsumo(${loteIndex}, ${insumoIndex}, 'tipo', this.value)">
                            <option value="uniforme" ${insumo.tipo === 'uniforme' ? 'selected' : ''}>Uniforme</option>
                            <option value="epi" ${insumo.tipo === 'epi' ? 'selected' : ''}>EPI</option>
                            <option value="material" ${insumo.tipo === 'material' ? 'selected' : ''}>Material</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Descrição</label>
                        <input type="text" class="form-control" value="${insumo.descricao || ''}"
                               onchange="atualizarInsumo(${loteIndex}, ${insumoIndex}, 'descricao', this.value)">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Custo Unit. (R$)</label>
                        <input type="number" class="form-control" value="${insumo.custo_unitario || 0}" step="0.01"
                               onchange="atualizarInsumo(${loteIndex}, ${insumoIndex}, 'custo_unitario', parseFloat(this.value))">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Qtd/Posto</label>
                        <input type="number" class="form-control" value="${insumo.quantidade_por_posto || 1}" min="1"
                               onchange="atualizarInsumo(${loteIndex}, ${insumoIndex}, 'quantidade_por_posto', parseInt(this.value))">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Reposição (meses)</label>
                        <input type="number" class="form-control" value="${insumo.periodicidade_meses || 12}" min="1"
                               onchange="atualizarInsumo(${loteIndex}, ${insumoIndex}, 'periodicidade_meses', parseInt(this.value))">
                    </div>
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="button" class="btn btn-danger w-100" onclick="removerInsumo(${loteIndex}, ${insumoIndex})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function ativarEventListenersLotes() {
    // Event listeners já estão inline no HTML (onclick)
}

function adicionarPosto(loteIndex) {
    const posto = {
        cargo: '',
        quantidade_postos: 1,
        jornada_tipo: '44h',
        salario_base: 0,
        adicional_insalubridade: 0,
        adicional_periculosidade: 0,
        adicional_noturno_percentual: 20.0,
        gratificacao: 0,
        vt_valor_unitario: 0,
        vt_dias: 0,
        vr_valor_dia: 0,
        vr_dias: 0,
        saude_mensal: 0,
        cesta_mensal: 0
    };
    
    lotes[loteIndex].postos.push(posto);
    renderizarLotes();
    salvarSessao();
}

function adicionarInsumo(loteIndex) {
    const insumo = {
        tipo: 'uniforme',
        descricao: '',
        custo_unitario: 0,
        quantidade_por_posto: 1,
        periodicidade_meses: 12,
        cargo: 'todos'
    };
    
    lotes[loteIndex].insumos.push(insumo);
    renderizarLotes();
    salvarSessao();
}

function atualizarPosto(loteIndex, postoIndex, campo, valor) {
    lotes[loteIndex].postos[postoIndex][campo] = valor;
    salvarSessao();
    atualizarResumo();
}

function atualizarInsumo(loteIndex, insumoIndex, campo, valor) {
    lotes[loteIndex].insumos[insumoIndex][campo] = valor;
    salvarSessao();
    atualizarResumo();
}

function removerLote(index) {
    if (confirm('Tem certeza que deseja remover este lote?')) {
        lotes.splice(index, 1);
        renderizarLotes();
        salvarSessao();
        atualizarResumo();
    }
}

function removerPosto(loteIndex, postoIndex) {
    lotes[loteIndex].postos.splice(postoIndex, 1);
    renderizarLotes();
    salvarSessao();
    atualizarResumo();
}

function removerInsumo(loteIndex, insumoIndex) {
    lotes[loteIndex].insumos.splice(insumoIndex, 1);
    renderizarLotes();
    salvarSessao();
    atualizarResumo();
}

// ============================================================
// PARÂMETROS E RESUMO
// ============================================================

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

function atualizarCamposTributos() {
    const regime = document.getElementById('regime_tributario')?.value;
    const campoPis = document.getElementById('campo-pis');
    const campoCofins = document.getElementById('campo-cofins');
    
    if (regime === 'simples') {
        if (campoPis) campoPis.style.display = 'none';
        if (campoCofins) campoCofins.style.display = 'none';
    } else {
        if (campoPis) campoPis.style.display = 'block';
        if (campoCofins) campoCofins.style.display = 'block';
    }
}

function atualizarResumo() {
    // Coletar todos os postos de todos os lotes
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
    
    if (todosPostos.length === 0) {
        return;
    }
    
    coletarParametros();
    
    // Chamar API de preview
    fetch('/precificaja/servicos/nova-lei/api/preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            postos: todosPostos,
            insumos: todosInsumos,
            parametros: parametros
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            const resultado = data.resultado;
            const totais = resultado.total_contrato;
            
            // Atualizar resumo
            document.getElementById('resumoRemuneracao').textContent = formatarMoeda(totais.total_remuneracao);
            document.getElementById('resumoEncargos').textContent = formatarMoeda(totais.total_encargos_beneficios);
            document.getElementById('resumoProvisoes').textContent = formatarMoeda(totais.total_provisoes);
            document.getElementById('resumoReposicao').textContent = formatarMoeda(totais.total_reposicao);
            document.getElementById('resumoInsumos').textContent = formatarMoeda(totais.total_insumos);
            document.getElementById('resumoSubtotal').textContent = formatarMoeda(totais.subtotal_antes_citl);
            
            document.getElementById('resumoCustosIndiretos').textContent = formatarMoeda(totais.custos_indiretos);
            document.getElementById('resumoTributos').textContent = formatarMoeda(totais.tributos);
            document.getElementById('resumoLucro').textContent = formatarMoeda(totais.lucro);
            document.getElementById('resumoPrecoTotal').textContent = formatarMoeda(totais.total_contrato);
            
            const margemLucro = (totais.lucro / totais.total_contrato * 100).toFixed(2);
            document.getElementById('resumoMargemLucro').textContent = margemLucro + '%';
        }
    })
    .catch(error => {
        console.error('Erro ao atualizar resumo:', error);
    });
}

// ============================================================
// FINALIZAÇÃO
// ============================================================

function finalizarPrecificacao() {
    if (lotes.length === 0 || lotes.every(l => l.postos.length === 0)) {
        alert('Adicione pelo menos um posto de trabalho!');
        return;
    }
    
    // Coletar todos os postos e insumos
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
    
    coletarParametros();
    
    // Salvar no banco
    const dados = {
        passo1: dadosPasso1,
        postos: todosPostos,
        insumos: todosInsumos,
        parametros: parametros
    };
    
    fetch('/precificaja/servicos/nova-lei/api/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarToast('Proposta salva com sucesso!', 'success');
            limparSessao();
            
            // Redirecionar para simulação
            setTimeout(() => {
                window.location.href = '/precificaja/servicos/nova-lei/simulacao';
            }, 1500);
        } else {
            alert('Erro ao salvar: ' + data.erro);
        }
    })
    .catch(error => {
        console.error('Erro ao salvar:', error);
        alert('Erro ao salvar proposta. Tente novamente.');
    });
}

// ============================================================
// SESSÃO E RECUPERAÇÃO
// ============================================================

function salvarSessao() {
    const sessao = {
        dadosPasso1: dadosPasso1,
        lotes: lotes,
        parametros: parametros,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('calculadora_nova_lei_sessao', JSON.stringify(sessao));
}

function carregarSessao() {
    const sessaoStr = localStorage.getItem('calculadora_nova_lei_sessao');
    
    if (!sessaoStr) {
        return null;
    }
    
    return JSON.parse(sessaoStr);
}

function limparSessao() {
    localStorage.removeItem('calculadora_nova_lei_sessao');
}

function verificarRecuperacaoSessao() {
    const sessao = carregarSessao();
    
    if (!sessao) {
        return;
    }
    
    // Verificar se a sessão tem menos de 24 horas
    const timestamp = new Date(sessao.timestamp);
    const agora = new Date();
    const diferencaHoras = (agora - timestamp) / (1000 * 60 * 60);
    
    if (diferencaHoras > 24) {
        limparSessao();
        return;
    }
    
    // Mostrar modal de recuperação
    const modal = new bootstrap.Modal(document.getElementById('recoveryModal'));
    modal.show();
    
    document.getElementById('continuarSessao').onclick = function() {
        dadosPasso1 = sessao.dadosPasso1;
        lotes = sessao.lotes;
        parametros = sessao.parametros;
        
        // Avançar para passo 2
        document.getElementById('passo1').style.display = 'none';
        document.getElementById('passo2').style.display = 'block';
        
        renderizarLotes();
        atualizarResumo();
        
        modal.hide();
        mostrarToast('Sessão recuperada!', 'success');
    };
    
    document.getElementById('novaSessao').onclick = function() {
        limparSessao();
        modal.hide();
    };
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
    const toast = document.getElementById('autoSaveToast');
    
    if (!toast) {
        return;
    }
    
    const toastBody = toast.querySelector('.toast-body');
    toastBody.textContent = mensagem;
    
    const toastHeader = toast.querySelector('.toast-header');
    toastHeader.className = `toast-header bg-${tipo} text-white`;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

/**
 * Calculadora Nova Lei - Edição Funcional
 * Carrega dados existentes para edição
 */

// Variáveis globais
let modoEdicao = false;
let cenarioIdEdicao = null;

// ============================================================
// INICIALIZAÇÃO
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    verificarModoEdicao();
});

// Variáveis globais para modo edição
let modoEdicao = false;
let cenarioIdEdicao = null;

function verificarModoEdicao() {
    // Tentar pegar do elemento hidden no HTML (prioridade)
    const cenarioIdInput = document.getElementById('cenario_id_edicao');
    if (cenarioIdInput && cenarioIdInput.value) {
        cenarioIdEdicao = parseInt(cenarioIdInput.value);
        modoEdicao = true;
        console.log(`✅ Modo de edição ativado para cenário ID: ${cenarioIdEdicao}`);
        carregarDadosEdicao(cenarioIdEdicao);
        return;
    }
    
    // Fallback: tentar pegar da URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('editar')) {
        const editarParam = urlParams.get('editar');
        if (editarParam && editarParam !== '1') {
            cenarioIdEdicao = parseInt(editarParam);
            modoEdicao = true;
            console.log(`✅ Modo de edição ativado para cenário ID: ${cenarioIdEdicao} (da URL)`);
            carregarDadosEdicao(cenarioIdEdicao);
            return;
        }
    }
    
    console.log('ℹ️ Modo de criação (novo cenário)');
}

function carregarDadosEdicao(cenarioId) {
    // Mostrar loading
    mostrarLoading('Carregando dados para edição...');
    
    // Chamar API para carregar dados
    fetch(`/precificaja/servicos/nova-lei/api/carregar/${cenarioId}`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                preencherFormulario(data.cenario);
                mostrarToast('Dados carregados com sucesso!', 'success');
            } else {
                mostrarToast('Erro ao carregar dados: ' + data.erro, 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao carregar dados:', error);
            mostrarToast('Erro ao carregar dados. Verifique sua conexão.', 'error');
        })
        .finally(() => {
            esconderLoading();
        });
}

function preencherFormulario(cenario) {
    console.log('Preenchendo formulário com dados:', cenario);
    
    // ============================================================
    // PASSO 1: Dados da Empresa e Órgão
    // ============================================================
    
    // Dados da empresa
    if (document.getElementById('cnpj')) {
        document.getElementById('cnpj').value = cenario.cnpj || '';
    }
    if (document.getElementById('razao_social')) {
        document.getElementById('razao_social').value = cenario.razao_social || '';
    }
    if (document.getElementById('endereco')) {
        document.getElementById('endereco').value = cenario.endereco || '';
    }
    
    // Dados do órgão
    if (document.getElementById('numero_processo')) {
        document.getElementById('numero_processo').value = cenario.numero_processo || '';
    }
    if (document.getElementById('validade_proposta')) {
        document.getElementById('validade_proposta').value = cenario.validade_proposta || '';
    }
    if (document.getElementById('prazo_pagamento')) {
        document.getElementById('prazo_pagamento').value = cenario.prazo_pagamento || '';
    }
    if (document.getElementById('local_execucao')) {
        document.getElementById('local_execucao').value = cenario.local_execucao || '';
    }
    if (document.getElementById('prazo_execucao')) {
        document.getElementById('prazo_execucao').value = cenario.prazo_execucao || '';
    }
    if (document.getElementById('tipo_servico')) {
        document.getElementById('tipo_servico').value = cenario.tipo_servico || '';
    }
    
    // ============================================================
    // PASSO 2: Parâmetros
    // ============================================================
    
    if (cenario.parametros) {
        const params = cenario.parametros;
        
        // Encargos
        if (document.getElementById('inss_patronal')) {
            document.getElementById('inss_patronal').value = params.inss_patronal || 20.0;
        }
        if (document.getElementById('salario_educacao')) {
            document.getElementById('salario_educacao').value = params.salario_educacao || 2.5;
        }
        if (document.getElementById('rat_sat')) {
            document.getElementById('rat_sat').value = params.rat_sat || 3.0;
        }
        if (document.getElementById('fap')) {
            document.getElementById('fap').value = params.fap_multiplicador || 1.0;
        }
        if (document.getElementById('sesc_senac')) {
            document.getElementById('sesc_senac').value = params.sesc_senac || 1.5;
        }
        if (document.getElementById('sebrae')) {
            document.getElementById('sebrae').value = params.sebrae || 0.6;
        }
        if (document.getElementById('incra')) {
            document.getElementById('incra').value = params.incra || 0.2;
        }
        
        // Tributos
        if (document.getElementById('regime_tributario')) {
            document.getElementById('regime_tributario').value = params.regime_tributario || 'simples';
            // Trigger change para mostrar/ocultar campos
            document.getElementById('regime_tributario').dispatchEvent(new Event('change'));
        }
        if (document.getElementById('aliquota_simples')) {
            document.getElementById('aliquota_simples').value = params.aliquota_simples || 14.0;
        }
        if (document.getElementById('aliquota_pis')) {
            document.getElementById('aliquota_pis').value = params.aliquota_pis || 0.65;
        }
        if (document.getElementById('aliquota_cofins')) {
            document.getElementById('aliquota_cofins').value = params.aliquota_cofins || 3.0;
        }
        if (document.getElementById('aliquota_iss')) {
            document.getElementById('aliquota_iss').value = params.aliquota_iss || 5.0;
        }
        
        // Custos indiretos e lucro
        if (document.getElementById('custos_indiretos')) {
            document.getElementById('custos_indiretos').value = params.custos_indiretos_percentual || 5.0;
        }
        if (document.getElementById('lucro_percentual')) {
            document.getElementById('lucro_percentual').value = params.lucro_percentual || 8.0;
            // Atualizar label do slider
            if (document.getElementById('lucro_valor')) {
                document.getElementById('lucro_valor').textContent = (params.lucro_percentual || 8.0) + '%';
            }
        }
    }
    
    // ============================================================
    // PASSO 2: Lotes, Postos e Insumos
    // ============================================================
    
    // Limpar lotes existentes
    window.lotes = [];
    
    // Organizar postos por lote
    const postosPorLote = {};
    if (cenario.postos && cenario.postos.length > 0) {
        cenario.postos.forEach(posto => {
            const loteNum = posto.lote_numero || 1;
            if (!postosPorLote[loteNum]) {
                postosPorLote[loteNum] = {
                    numero: loteNum,
                    nome: posto.lote_nome || `Lote ${loteNum}`,
                    postos: [],
                    insumos: []
                };
            }
            
            // Adicionar posto com todos os dados
            postosPorLote[loteNum].postos.push({
                cargo: posto.cargo,
                quantidade_postos: posto.quantidade_postos,
                jornada_tipo: posto.jornada_tipo,
                salario_base: posto.salario_base,
                adicional_insalubridade: posto.adicional_insalubridade || 0,
                adicional_periculosidade: posto.adicional_periculosidade || 0,
                adicional_noturno_percentual: posto.adicional_noturno_percentual || 0,
                gratificacao: posto.gratificacao || 0
            });
        });
    }
    
    // Organizar insumos por lote
    if (cenario.insumos && cenario.insumos.length > 0) {
        cenario.insumos.forEach(insumo => {
            const loteNum = insumo.lote_numero || 1;
            if (!postosPorLote[loteNum]) {
                postosPorLote[loteNum] = {
                    numero: loteNum,
                    nome: `Lote ${loteNum}`,
                    postos: [],
                    insumos: []
                };
            }
            
            // Adicionar insumo com todos os dados
            postosPorLote[loteNum].insumos.push({
                tipo: insumo.tipo,
                descricao: insumo.descricao,
                custo_unitario: insumo.custo_unitario,
                quantidade_por_posto: insumo.quantidade_por_posto,
                periodicidade_meses: insumo.periodicidade_meses,
                cargo: insumo.cargo
            });
        });
    }
    
    // Criar array de lotes ordenado
    Object.keys(postosPorLote).sort((a, b) => parseInt(a) - parseInt(b)).forEach(loteNum => {
        window.lotes.push(postosPorLote[loteNum]);
    });
    
    console.log('Lotes carregados:', window.lotes);
    
    // Renderizar lotes na interface
    if (typeof renderizarLotes === 'function') {
        console.log('Renderizando lotes...');
        renderizarLotes();
    } else {
        console.error('Função renderizarLotes não encontrada!');
    }
    
    // Recalcular resumo após renderizar
    setTimeout(() => {
        if (typeof atualizarResumo === 'function') {
            console.log('Atualizando resumo...');
            atualizarResumo();
        }
    }, 1000);
    
    console.log('Formulário preenchido com sucesso!');
    
    // ============================================================
    // AUTO-AVANÇAR PARA PASSO 2
    // ============================================================
    
    setTimeout(() => {
        avancarParaPasso2();
    }, 800);
}

// ============================================================
// AVANÇAR PARA PASSO 2
// ============================================================

function avancarParaPasso2() {
    console.log('Auto-avançando para Passo 2...');
    
    // Método 1: Tentar clicar no botão "Próximo"
    const btnProximo = document.querySelector('button[onclick*="proximoPasso"]') || 
                       document.querySelector('button[onclick*="passo2"]') ||
                       document.getElementById('btnProximoPasso');
    
    if (btnProximo) {
        console.log('Clicando no botão Próximo...');
        btnProximo.click();
        return;
    }
    
    // Método 2: Tentar usar função global proximoPasso()
    if (typeof proximoPasso === 'function') {
        console.log('Chamando função proximoPasso()...');
        proximoPasso();
        return;
    }
    
    // Método 3: Manipular diretamente os passos
    const passo1 = document.getElementById('passo1');
    const passo2 = document.getElementById('passo2');
    
    if (passo1 && passo2) {
        console.log('Manipulando passos diretamente...');
        passo1.style.display = 'none';
        passo1.classList.remove('active');
        
        passo2.style.display = 'block';
        passo2.classList.add('active');
        
        // Atualizar indicadores de passo
        const indicadorPasso1 = document.querySelector('[data-passo="1"]');
        const indicadorPasso2 = document.querySelector('[data-passo="2"]');
        
        if (indicadorPasso1) {
            indicadorPasso1.classList.remove('active');
            indicadorPasso1.classList.add('completed');
        }
        
        if (indicadorPasso2) {
            indicadorPasso2.classList.add('active');
        }
        
        // Scroll para o topo
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Mostrar toast
        mostrarToast('Dados carregados! Você pode editar os valores abaixo.', 'success');
        
        return;
    }
    
    // Método 4: Tentar com Bootstrap tabs
    const tabPasso2 = document.querySelector('a[href="#passo2"]') || 
                      document.querySelector('button[data-bs-target="#passo2"]');
    
    if (tabPasso2) {
        console.log('Ativando tab do Passo 2...');
        
        // Bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
            const tab = new bootstrap.Tab(tabPasso2);
            tab.show();
            mostrarToast('Dados carregados! Você pode editar os valores abaixo.', 'success');
            return;
        }
        
        // Bootstrap 4 ou jQuery
        if (typeof $ !== 'undefined' && $.fn.tab) {
            $(tabPasso2).tab('show');
            mostrarToast('Dados carregados! Você pode editar os valores abaixo.', 'success');
            return;
        }
        
        // Fallback: click
        tabPasso2.click();
        mostrarToast('Dados carregados! Você pode editar os valores abaixo.', 'success');
        return;
    }
    
    console.warn('Não foi possível avançar automaticamente para o Passo 2');
    mostrarToast('Dados carregados! Clique em "Próximo" para continuar.', 'info');
}

// ============================================================
// SALVAR EDIÇÃO
// ============================================================

function salvarEdicao() {
    if (!modoEdicao || !cenarioIdEdicao) {
        console.error('Não está em modo de edição');
        return;
    }
    
    console.log('Salvando edição do cenário:', cenarioIdEdicao);
    
    // Coletar dados do Passo 1
    const dadosPasso1 = {
        cnpj: document.getElementById('cnpj')?.value || '',
        razao_social: document.getElementById('razao_social')?.value || '',
        endereco: document.getElementById('endereco')?.value || '',
        numero_processo: document.getElementById('numero_processo')?.value || '',
        validade_proposta: parseInt(document.getElementById('validade_proposta')?.value) || 60,
        prazo_pagamento: parseInt(document.getElementById('prazo_pagamento')?.value) || 30,
        local_execucao: document.getElementById('local_execucao')?.value || '',
        prazo_execucao: parseInt(document.getElementById('prazo_execucao')?.value) || 12,
        tipo_servico: document.getElementById('tipo_servico')?.value || ''
    };
    
    // Coletar parâmetros
    const parametros = {
        inss_patronal: parseFloat(document.getElementById('inss_patronal')?.value) || 20.0,
        salario_educacao: parseFloat(document.getElementById('salario_educacao')?.value) || 2.5,
        rat_sat: parseFloat(document.getElementById('rat_sat')?.value) || 3.0,
        fap_multiplicador: parseFloat(document.getElementById('fap')?.value) || 1.0,
        sesc_senac: parseFloat(document.getElementById('sesc_senac')?.value) || 1.5,
        sebrae: parseFloat(document.getElementById('sebrae')?.value) || 0.6,
        incra: parseFloat(document.getElementById('incra')?.value) || 0.2,
        regime_tributario: document.getElementById('regime_tributario')?.value || 'simples',
        aliquota_simples: parseFloat(document.getElementById('aliquota_simples')?.value) || 14.0,
        aliquota_pis: parseFloat(document.getElementById('aliquota_pis')?.value) || 0.65,
        aliquota_cofins: parseFloat(document.getElementById('aliquota_cofins')?.value) || 3.0,
        aliquota_iss: parseFloat(document.getElementById('aliquota_iss')?.value) || 5.0,
        custos_indiretos_percentual: parseFloat(document.getElementById('custos_indiretos')?.value) || 5.0,
        lucro_percentual: parseFloat(document.getElementById('lucro_percentual')?.value) || 8.0
    };
    
    // Coletar postos e insumos dos lotes
    const postos = [];
    const insumos = [];
    
    if (window.lotes && window.lotes.length > 0) {
        window.lotes.forEach(lote => {
            // Postos
            if (lote.postos && lote.postos.length > 0) {
                lote.postos.forEach(posto => {
                    postos.push({
                        lote_numero: lote.numero,
                        lote_nome: lote.nome,
                        cargo: posto.cargo,
                        quantidade_postos: posto.quantidade_postos,
                        jornada_tipo: posto.jornada_tipo,
                        salario_base: posto.salario_base,
                        adicional_insalubridade: posto.adicional_insalubridade || 0,
                        adicional_periculosidade: posto.adicional_periculosidade || 0,
                        adicional_noturno_percentual: posto.adicional_noturno_percentual || 0,
                        gratificacao: posto.gratificacao || 0
                    });
                });
            }
            
            // Insumos
            if (lote.insumos && lote.insumos.length > 0) {
                lote.insumos.forEach(insumo => {
                    insumos.push({
                        lote_numero: lote.numero,
                        tipo: insumo.tipo,
                        descricao: insumo.descricao,
                        custo_unitario: insumo.custo_unitario,
                        quantidade_por_posto: insumo.quantidade_por_posto,
                        periodicidade_meses: insumo.periodicidade_meses,
                        cargo: insumo.cargo
                    });
                });
            }
        });
    }
    
    // Montar payload completo
    const dados = {
        passo1: dadosPasso1,
        parametros: parametros,
        postos: postos,
        insumos: insumos
    };
    
    // Adicionar cenario_id SOMENTE se estiver em modo edição
    if (modoEdicao && cenarioIdEdicao) {
        dados.cenario_id = cenarioIdEdicao;  // ← IMPORTANTE: ID para UPDATE
        console.log(`🔄 Atualizando cenário existente ID: ${cenarioIdEdicao}`);
    } else {
        console.log('➕ Criando novo cenário');
    }
    
    console.log('Dados para salvar:', dados);
    
    // Mostrar loading
    mostrarLoading('Salvando alterações...');
    
    // Enviar para API
    fetch('/precificaja/servicos/nova-lei/api/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        esconderLoading();
        
        if (data.sucesso) {
            mostrarToast('✅ Alterações salvas com sucesso!', 'success');
            
            // Limpar localStorage
            localStorage.removeItem('calculadoraNovaLei_passo1');
            localStorage.removeItem('calculadoraNovaLei_lotes');
            
            // Redirecionar para simulação
            setTimeout(() => {
                window.location.href = '/precificaja/servicos/nova-lei/simulacao';
            }, 1500);
        } else {
            mostrarToast('❌ Erro ao salvar: ' + data.erro, 'error');
        }
    })
    .catch(error => {
        esconderLoading();
        console.error('Erro ao salvar:', error);
        mostrarToast('❌ Erro ao salvar alterações', 'error');
    });
}

// ============================================================
// UTILITÁRIOS
// ============================================================

function mostrarLoading(mensagem) {
    // Criar overlay de loading
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    
    overlay.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Carregando...</span>
            </div>
            <p class="mt-3 mb-0">${mensagem}</p>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

function esconderLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

function mostrarToast(mensagem, tipo = 'info') {
    // Criar toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo === 'success' ? 'success' : tipo === 'error' ? 'danger' : 'info'} position-fixed`;
    toast.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    toast.textContent = mensagem;
    
    document.body.appendChild(toast);
    
    // Remover após 3 segundos
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Expor funções globalmente
window.modoEdicao = modoEdicao;
window.cenarioIdEdicao = cenarioIdEdicao;
window.salvarEdicao = salvarEdicao;

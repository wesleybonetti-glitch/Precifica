/**
 * Modal de Edição - JavaScript
 * Sistema isolado para edição de propostas
 */

// Variáveis globais do modal
let modalLotes = [];
let modalCenarioId = null;

// ============================================================
// ABRIR MODAL DE EDIÇÃO
// ============================================================

function abrirModalEdicao(cenarioId) {
    console.log(`📝 Abrindo modal de edição para cenário ID: ${cenarioId}`);
    
    modalCenarioId = cenarioId;
    modalLotes = [];
    
    // Carregar dados
    fetch(`/precificaja/servicos/nova-lei/api/carregar/${cenarioId}`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                preencherModalEdicao(data.cenario);
                
                // Abrir modal
                const modal = new bootstrap.Modal(document.getElementById('modalEdicao'));
                modal.show();
            } else {
                alert('Erro ao carregar dados: ' + data.erro);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao carregar proposta');
        });
}

// ============================================================
// PREENCHER MODAL COM DADOS
// ============================================================

function preencherModalEdicao(cenario) {
    console.log('Preenchendo modal com dados:', cenario);
    
    // ID
    document.getElementById('edit_cenario_id').value = cenario.id;
    
    // Tab 1: Dados da Proposta
    document.getElementById('edit_cnpj').value = cenario.cnpj || '';
    document.getElementById('edit_razao_social').value = cenario.razao_social || '';
    document.getElementById('edit_endereco').value = cenario.endereco || '';
    document.getElementById('edit_numero_processo').value = cenario.numero_processo || '';
    document.getElementById('edit_tipo_servico').value = cenario.tipo_servico || 'limpeza';
    document.getElementById('edit_validade_proposta').value = cenario.validade_proposta || 60;
    document.getElementById('edit_prazo_pagamento').value = cenario.prazo_pagamento || 30;
    document.getElementById('edit_prazo_execucao').value = cenario.prazo_execucao || 12;
    document.getElementById('edit_local_execucao').value = cenario.local_execucao || '';
    
    // Tab 3: Parâmetros
    document.getElementById('edit_inss_patronal').value = cenario.inss_patronal || 20.0;
    document.getElementById('edit_salario_educacao').value = cenario.salario_educacao || 2.5;
    document.getElementById('edit_rat_sat').value = cenario.rat_sat || 3.0;
    document.getElementById('edit_fap').value = cenario.fap_multiplicador || 1.0;
    document.getElementById('edit_regime_tributario').value = cenario.regime_tributario || 'simples';
    document.getElementById('edit_aliquota_simples').value = cenario.aliquota_simples || 14.0;
    document.getElementById('edit_custos_indiretos').value = cenario.custos_indiretos_percentual || 5.0;
    document.getElementById('edit_lucro_percentual').value = cenario.lucro_percentual || 8.0;
    
    // Tab 2: Lotes e Postos
    organizarLotesModal(cenario.postos, cenario.insumos);
    renderizarLotesModal();
    
    // Tab 4: Calcular e mostrar resumo
    setTimeout(() => {
        calcularResumoModal();
    }, 500);
}

// ============================================================
// ORGANIZAR LOTES
// ============================================================

function organizarLotesModal(postos, insumos) {
    modalLotes = [];
    const lotesPorNumero = {};
    
    // Organizar postos por lote
    if (postos && postos.length > 0) {
        postos.forEach(posto => {
            const loteNum = posto.lote_numero || 1;
            if (!lotesPorNumero[loteNum]) {
                lotesPorNumero[loteNum] = {
                    numero: loteNum,
                    nome: posto.lote_nome || `Lote ${loteNum}`,
                    postos: [],
                    insumos: []
                };
            }
            lotesPorNumero[loteNum].postos.push({
                cargo: posto.cargo,
                quantidade_postos: posto.quantidade_postos,
                jornada_tipo: posto.jornada_tipo,
                salario_base: posto.salario_base,
                adicional_insalubridade: posto.adicional_insalubridade || 0,
                adicional_periculosidade: posto.adicional_periculosidade || 0
            });
        });
    }
    
    // Organizar insumos por lote
    if (insumos && insumos.length > 0) {
        insumos.forEach(insumo => {
            const loteNum = insumo.lote_numero || 1;
            if (!lotesPorNumero[loteNum]) {
                lotesPorNumero[loteNum] = {
                    numero: loteNum,
                    nome: `Lote ${loteNum}`,
                    postos: [],
                    insumos: []
                };
            }
            lotesPorNumero[loteNum].insumos.push({
                tipo: insumo.tipo,
                descricao: insumo.descricao,
                custo_unitario: insumo.custo_unitario,
                quantidade_por_posto: insumo.quantidade_por_posto,
                periodicidade_meses: insumo.periodicidade_meses
            });
        });
    }
    
    // Converter para array
    Object.keys(lotesPorNumero).sort((a, b) => parseInt(a) - parseInt(b)).forEach(loteNum => {
        modalLotes.push(lotesPorNumero[loteNum]);
    });
    
    console.log('Lotes organizados:', modalLotes);
}

// ============================================================
// RENDERIZAR LOTES NO MODAL
// ============================================================

function renderizarLotesModal() {
    const container = document.getElementById('edit_lotes_container');
    
    if (modalLotes.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum lote cadastrado. Clique em "Adicionar Lote" para começar.</p>';
        return;
    }
    
    let html = '';
    
    modalLotes.forEach((lote, loteIndex) => {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-primary text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-layer-group"></i>
                            <input type="text" class="form-control form-control-sm d-inline-block" 
                                   style="width: 200px; background: white;" 
                                   value="${lote.nome}" 
                                   onchange="modalLotes[${loteIndex}].nome = this.value">
                        </div>
                        <button type="button" class="btn btn-sm btn-danger" onclick="removerLoteModal(${loteIndex})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <!-- Postos -->
                    <h6 class="text-primary"><i class="fas fa-users"></i> Postos de Trabalho</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered">
                            <thead>
                                <tr>
                                    <th>Cargo</th>
                                    <th>Qtd</th>
                                    <th>Jornada</th>
                                    <th>Salário Base</th>
                                    <th>Insalubridade</th>
                                    <th>Periculosidade</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${lote.postos.map((posto, postoIndex) => `
                                    <tr>
                                        <td><input type="text" class="form-control form-control-sm" value="${posto.cargo}" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].cargo = this.value"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${posto.quantidade_postos}" min="1" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].quantidade_postos = parseInt(this.value)"></td>
                                        <td>
                                            <select class="form-select form-select-sm" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].jornada_tipo = this.value">
                                                <option value="44h" ${posto.jornada_tipo === '44h' ? 'selected' : ''}>44h</option>
                                                <option value="40h" ${posto.jornada_tipo === '40h' ? 'selected' : ''}>40h</option>
                                                <option value="12x36_diurno" ${posto.jornada_tipo === '12x36_diurno' ? 'selected' : ''}>12x36 Diurno</option>
                                                <option value="12x36_noturno" ${posto.jornada_tipo === '12x36_noturno' ? 'selected' : ''}>12x36 Noturno</option>
                                            </select>
                                        </td>
                                        <td><input type="number" class="form-control form-control-sm" value="${posto.salario_base}" step="0.01" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].salario_base = parseFloat(this.value)"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${posto.adicional_insalubridade}" step="0.01" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].adicional_insalubridade = parseFloat(this.value)"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${posto.adicional_periculosidade}" step="0.01" onchange="modalLotes[${loteIndex}].postos[${postoIndex}].adicional_periculosidade = parseFloat(this.value)"></td>
                                        <td>
                                            <button type="button" class="btn btn-sm btn-danger" onclick="removerPostoModal(${loteIndex}, ${postoIndex})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    <button type="button" class="btn btn-sm btn-success" onclick="adicionarPostoModal(${loteIndex})">
                        <i class="fas fa-plus"></i> Adicionar Posto
                    </button>
                    
                    <!-- Insumos -->
                    <h6 class="text-primary mt-4"><i class="fas fa-box"></i> Insumos</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered">
                            <thead>
                                <tr>
                                    <th>Tipo</th>
                                    <th>Descrição</th>
                                    <th>Custo Unit.</th>
                                    <th>Qtd/Posto</th>
                                    <th>Periodicidade (meses)</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${lote.insumos.map((insumo, insumoIndex) => `
                                    <tr>
                                        <td>
                                            <select class="form-select form-select-sm" onchange="modalLotes[${loteIndex}].insumos[${insumoIndex}].tipo = this.value">
                                                <option value="uniforme" ${insumo.tipo === 'uniforme' ? 'selected' : ''}>Uniforme</option>
                                                <option value="epi" ${insumo.tipo === 'epi' ? 'selected' : ''}>EPI</option>
                                                <option value="material" ${insumo.tipo === 'material' ? 'selected' : ''}>Material</option>
                                            </select>
                                        </td>
                                        <td><input type="text" class="form-control form-control-sm" value="${insumo.descricao}" onchange="modalLotes[${loteIndex}].insumos[${insumoIndex}].descricao = this.value"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${insumo.custo_unitario}" step="0.01" onchange="modalLotes[${loteIndex}].insumos[${insumoIndex}].custo_unitario = parseFloat(this.value)"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${insumo.quantidade_por_posto}" step="0.1" onchange="modalLotes[${loteIndex}].insumos[${insumoIndex}].quantidade_por_posto = parseFloat(this.value)"></td>
                                        <td><input type="number" class="form-control form-control-sm" value="${insumo.periodicidade_meses}" min="1" onchange="modalLotes[${loteIndex}].insumos[${insumoIndex}].periodicidade_meses = parseInt(this.value)"></td>
                                        <td>
                                            <button type="button" class="btn btn-sm btn-danger" onclick="removerInsumoModal(${loteIndex}, ${insumoIndex})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    <button type="button" class="btn btn-sm btn-warning" onclick="adicionarInsumoModal(${loteIndex})">
                        <i class="fas fa-plus"></i> Adicionar Insumo
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================
// ADICIONAR/REMOVER LOTES, POSTOS E INSUMOS
// ============================================================

function adicionarLoteModal() {
    const novoNumero = modalLotes.length + 1;
    modalLotes.push({
        numero: novoNumero,
        nome: `Lote ${novoNumero}`,
        postos: [],
        insumos: []
    });
    renderizarLotesModal();
}

function removerLoteModal(index) {
    if (confirm('Deseja remover este lote?')) {
        modalLotes.splice(index, 1);
        renderizarLotesModal();
    }
}

function adicionarPostoModal(loteIndex) {
    modalLotes[loteIndex].postos.push({
        cargo: '',
        quantidade_postos: 1,
        jornada_tipo: '44h',
        salario_base: 0,
        adicional_insalubridade: 0,
        adicional_periculosidade: 0
    });
    renderizarLotesModal();
}

function removerPostoModal(loteIndex, postoIndex) {
    modalLotes[loteIndex].postos.splice(postoIndex, 1);
    renderizarLotesModal();
}

function adicionarInsumoModal(loteIndex) {
    modalLotes[loteIndex].insumos.push({
        tipo: 'uniforme',
        descricao: '',
        custo_unitario: 0,
        quantidade_por_posto: 1,
        periodicidade_meses: 12
    });
    renderizarLotesModal();
}

function removerInsumoModal(loteIndex, insumoIndex) {
    modalLotes[loteIndex].insumos.splice(insumoIndex, 1);
    renderizarLotesModal();
}

// ============================================================
// SALVAR EDIÇÃO
// ============================================================

// ============================================================
// CALCULAR E MOSTRAR RESUMO FINANCEIRO
// ============================================================

function calcularResumoModal() {
    console.log('📊 Calculando resumo financeiro...');
    
    // Coletar dados para cálculo
    const cenarioId = document.getElementById('edit_cenario_id').value;
    
    if (!cenarioId) {
        console.log('⚠️ Cenário ID não encontrado');
        return;
    }
    
    // Buscar resultado calculado
    fetch(`/precificaja/servicos/nova-lei/api/preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            parametros: {
                inss_patronal: parseFloat(document.getElementById('edit_inss_patronal').value) || 20,
                salario_educacao: parseFloat(document.getElementById('edit_salario_educacao').value) || 2.5,
                rat_sat: parseFloat(document.getElementById('edit_rat_sat').value) || 3,
                fap_multiplicador: parseFloat(document.getElementById('edit_fap').value) || 1.0,
                regime_tributario: document.getElementById('edit_regime_tributario').value || 'simples',
                aliquota_simples: parseFloat(document.getElementById('edit_aliquota_simples').value) || 6,
                custos_indiretos_percentual: parseFloat(document.getElementById('edit_custos_indiretos').value) || 5,
                lucro_percentual: parseFloat(document.getElementById('edit_lucro_percentual').value) || 8
            },
            postos: modalLotes.flatMap(lote => lote.postos.map(p => ({...p, lote_numero: lote.numero}))),
            insumos: modalLotes.flatMap(lote => lote.insumos.map(i => ({...i, lote_numero: lote.numero})))
        })
    })
    .then(response => {
        console.log('📥 Resposta da API preview recebida');
        return response.json();
    })
    .then(data => {
        console.log('📊 Dados recebidos:', data);
        
        if (!data.sucesso) {
            console.error('❌ API retornou erro:', data.erro);
            alert('Erro ao calcular resumo: ' + data.erro);
            return;
        }
        
        if (!data.resultado) {
            console.error('❌ API não retornou resultado');
            return;
        }
        
        const r = data.resultado;
        console.log('📈 Resultado completo:', r);
        
        // Os valores estão dentro de total_contrato!
        const totais = r.total_contrato || {};
        console.log('📊 Totais:', totais);
        console.log('📊 Valores recebidos:');
        console.log('  - total_remuneracao:', totais.total_remuneracao);
        console.log('  - total_encargos_beneficios:', totais.total_encargos_beneficios);
        console.log('  - total_provisoes:', totais.total_provisoes);
        console.log('  - total_reposicao:', totais.total_reposicao);
        console.log('  - total_insumos:', totais.total_insumos);
        console.log('  - subtotal_antes_citl:', totais.subtotal_antes_citl);
        console.log('  - custos_indiretos:', totais.custos_indiretos);
        console.log('  - tributos:', totais.tributos);
        console.log('  - lucro:', totais.lucro);
        console.log('  - total_contrato:', totais.total_contrato);
        
        // Verificar se elementos existem
        const elementos = [
            'resumo_remuneracao', 'resumo_encargos', 'resumo_provisoes',
            'resumo_reposicao', 'resumo_insumos', 'resumo_subtotal',
            'resumo_custos_indiretos', 'resumo_tributos', 'resumo_lucro',
            'resumo_total', 'resumo_total_postos', 'resumo_margem_lucro'
        ];
        
        const faltando = elementos.filter(id => !document.getElementById(id));
        if (faltando.length > 0) {
            console.error('❌ Elementos HTML faltando:', faltando);
            return;
        }
        
        // Preencher cards de custos diretos (nomes corretos do motor)
        try {
            const elemRemuneracao = document.getElementById('resumo_remuneracao');
            if (elemRemuneracao) {
                const valor = formatarMoeda(totais.total_remuneracao || 0);
                elemRemuneracao.textContent = valor;
                console.log('  ✅ resumo_remuneracao =', valor);
            } else {
                console.error('  ❌ Elemento resumo_remuneracao não encontrado');
            }
            
            const elemEncargos = document.getElementById('resumo_encargos');
            if (elemEncargos) {
                const valor = formatarMoeda(totais.total_encargos_beneficios || 0);
                elemEncargos.textContent = valor;
                console.log('  ✅ resumo_encargos =', valor);
            }
            
            const elemProvisoes = document.getElementById('resumo_provisoes');
            if (elemProvisoes) {
                const valor = formatarMoeda(totais.total_provisoes || 0);
                elemProvisoes.textContent = valor;
                console.log('  ✅ resumo_provisoes =', valor);
            }
            
            const elemReposicao = document.getElementById('resumo_reposicao');
            if (elemReposicao) {
                const valor = formatarMoeda(totais.total_reposicao || 0);
                elemReposicao.textContent = valor;
                console.log('  ✅ resumo_reposicao =', valor);
            }
            
            const elemInsumos = document.getElementById('resumo_insumos');
            if (elemInsumos) {
                const valor = formatarMoeda(totais.total_insumos || 0);
                elemInsumos.textContent = valor;
                console.log('  ✅ resumo_insumos =', valor);
            }
            
            const elemSubtotal = document.getElementById('resumo_subtotal');
            if (elemSubtotal) {
                const valor = formatarMoeda(totais.subtotal_antes_citl || 0);
                elemSubtotal.textContent = valor;
                console.log('  ✅ resumo_subtotal =', valor);
            }
            
            console.log('✅ Custos diretos preenchidos');
            
            // Preencher cards de CITL
            document.getElementById('resumo_custos_indiretos').textContent = formatarMoeda(totais.custos_indiretos || 0);
            document.getElementById('resumo_tributos').textContent = formatarMoeda(totais.tributos || 0);
            document.getElementById('resumo_lucro').textContent = formatarMoeda(totais.lucro || 0);
            
            console.log('✅ CITL preenchido');
            
            // Total
            document.getElementById('resumo_total').textContent = formatarMoeda(totais.total_contrato || 0);
            
            console.log('✅ Total preenchido');
            
            // Extras
            const totalPostos = modalLotes.reduce((sum, lote) => 
                sum + lote.postos.reduce((s, p) => s + (p.quantidade_postos || 0), 0), 0);
            document.getElementById('resumo_total_postos').textContent = totalPostos;
            
            // Calcular margem de lucro
            const subtotal = parseFloat(totais.subtotal_antes_citl || 0);
            const lucro = parseFloat(totais.lucro || 0);
            const margemLucro = subtotal > 0 ? (lucro / subtotal * 100) : 0;
            document.getElementById('resumo_margem_lucro').textContent = margemLucro.toFixed(2) + '%';
            
            console.log('✅ Extras preenchidos');
            console.log('✅ Resumo calculado e exibido com sucesso!');
            
        } catch (error) {
            console.error('❌ Erro ao preencher elementos:', error);
        }
    })
    .catch(error => {
        console.error('❌ Erro ao calcular resumo:', error);
        alert('Erro ao calcular resumo. Veja o console para detalhes.');
    });
}

function formatarMoeda(valor) {
    return 'R$ ' + parseFloat(valor || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// ============================================================
// SALVAR EDIÇÃO
// ============================================================

function salvarEdicaoModal() {
    console.log('💾 Salvando alterações...');
    
    // Coletar dados do formulário
    const dados = {
        cenario_id: parseInt(document.getElementById('edit_cenario_id').value),
        passo1: {
            cnpj: document.getElementById('edit_cnpj').value,
            razao_social: document.getElementById('edit_razao_social').value,
            endereco: document.getElementById('edit_endereco').value,
            numero_processo: document.getElementById('edit_numero_processo').value,
            tipo_servico: document.getElementById('edit_tipo_servico').value,
            validade_proposta: parseInt(document.getElementById('edit_validade_proposta').value),
            prazo_pagamento: parseInt(document.getElementById('edit_prazo_pagamento').value),
            prazo_execucao: parseInt(document.getElementById('edit_prazo_execucao').value),
            local_execucao: document.getElementById('edit_local_execucao').value
        },
        parametros: {
            inss_patronal: parseFloat(document.getElementById('edit_inss_patronal').value),
            salario_educacao: parseFloat(document.getElementById('edit_salario_educacao').value),
            rat_sat: parseFloat(document.getElementById('edit_rat_sat').value),
            fap_multiplicador: parseFloat(document.getElementById('edit_fap').value),
            regime_tributario: document.getElementById('edit_regime_tributario').value,
            aliquota_simples: parseFloat(document.getElementById('edit_aliquota_simples').value),
            custos_indiretos_percentual: parseFloat(document.getElementById('edit_custos_indiretos').value),
            lucro_percentual: parseFloat(document.getElementById('edit_lucro_percentual').value)
        },
        postos: [],
        insumos: []
    };
    
    // Coletar postos e insumos dos lotes
    modalLotes.forEach(lote => {
        lote.postos.forEach(posto => {
            dados.postos.push({
                lote_numero: lote.numero,
                lote_nome: lote.nome,
                ...posto
            });
        });
        
        lote.insumos.forEach(insumo => {
            dados.insumos.push({
                lote_numero: lote.numero,
                ...insumo
            });
        });
    });
    
    console.log('Dados para salvar:', dados);
    console.log('Parâmetros:', dados.parametros);
    console.log('Postos:', dados.postos.length);
    console.log('Insumos:', dados.insumos.length);
    
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
        if (data.sucesso) {
            alert('✅ Alterações salvas com sucesso!');
            
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEdicao'));
            modal.hide();
            
            // Recarregar página
            window.location.reload();
        } else {
            alert('❌ Erro ao salvar: ' + data.erro);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('❌ Erro ao salvar alterações');
    });
}


// Event listener para recalcular resumo ao clicar na tab
document.addEventListener('DOMContentLoaded', function() {
    const tabResumo = document.getElementById('tab-resumo');
    if (tabResumo) {
        tabResumo.addEventListener('click', function() {
            setTimeout(() => {
                calcularResumoModal();
            }, 200);
        });
    }
});

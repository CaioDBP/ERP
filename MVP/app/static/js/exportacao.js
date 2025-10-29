// Lógica de exportação de planilhas
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const pedidosTableBody = document.getElementById('pedidos-export-table-body');
    const selectAllCheckbox = document.getElementById('select-all-pedidos');
    const generateBtn = document.getElementById('generate-selected-planilha-btn');
    const noPedidosMsg = document.getElementById('no-pedidos-export-message');
    const exportMsg = document.getElementById('export-message');
    const contadorSelecionados = document.getElementById('pedidosSelecionados');

    // Mensagens de feedback
    function showExportMessage(message, success = true) {
        exportMsg.innerText = message;
        exportMsg.classList.remove('hidden');
        exportMsg.classList.toggle('text-green-600', success);
        exportMsg.classList.toggle('text-red-600', !success);
    }

    // Carrega pedidos confirmados
    async function loadPedidos(filters = {}) {
        pedidosTableBody.innerHTML = '';
        noPedidosMsg.classList.add('hidden');
        selectAllCheckbox.checked = false;
        contadorSelecionados.textContent = '0';

        const userId = localStorage.getItem('userId');
        if (!userId) {
            showExportMessage('Você precisa estar logado.', false);
            return;
        }

        try {
            const params = new URLSearchParams({ status: 'confirmado', ...filters });
            const response = await fetch(`/api/pedidos?${params.toString()}`, {
                headers: { 'X-User-Id': userId }
            });

            const pedidos = await response.json();

            if (response.ok && pedidos.length > 0) {

                noPedidosMsg.classList.add('hidden'); // linha adicionada

                pedidos.forEach(pedido => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><input type="checkbox" class="pedido-checkbox" data-id="${pedido.id}"></td>
                        <td>${pedido.clienteNome}</td>
                        <td>${pedido.dataRetirada || '-'}</td>
                        <td>${pedido.tipoPedido}</td>
                        <td>${pedido.quantidade}</td>
                        <td><span class="badge ${pedido.status === 'confirmado' ? 'badge-success' : 'badge-warning'}">${pedido.status}</span></td>
                    `;
                    pedidosTableBody.appendChild(row);
                });
            } else {
                noPedidosMsg.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Erro ao carregar pedidos:', err);
            showExportMessage('Erro ao carregar pedidos.', false);
        }
    }

    // Atualiza contador
    function atualizarContador() {
        const selecionados = document.querySelectorAll('.pedido-checkbox:checked').length;
        contadorSelecionados.textContent = selecionados;
    }

    // Checkbox "Selecionar Todos"
    selectAllCheckbox.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.pedido-checkbox');
        checkboxes.forEach(cb => (cb.checked = selectAllCheckbox.checked));
        atualizarContador();
    });

    // Quando marcar/desmarcar uma linha individual
    pedidosTableBody.addEventListener('change', e => {
        if (e.target.classList.contains('pedido-checkbox')) atualizarContador();
    });

    // Filtros
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const dataInicio = document.getElementById('dataInicio').value;
        const dataFim = document.getElementById('dataFim').value;
        const cliente = document.getElementById('cliente').value.trim();
        const filters = {};
        if (dataInicio) filters.dataInicio = dataInicio;
        if (dataFim) filters.dataFim = dataFim;
        if (cliente) filters.cliente = cliente;
        loadPedidos(filters);
    });

    // Gera planilha
    generateBtn.addEventListener('click', async function() {
        const selecionados = [...document.querySelectorAll('.pedido-checkbox:checked')].map(cb => cb.dataset.id);

        if (selecionados.length === 0) {
            showExportMessage('Selecione pelo menos um pedido.', false);
            return;
        }

        const userId = localStorage.getItem('userId');
        try {
            const response = await fetch('/api/reports/export-selected-pedidos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Id': userId
                },
                body: JSON.stringify({ pedido_ids: selecionados })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `planilha_producao_${new Date().toISOString().slice(0,10)}.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                showExportMessage('Planilha gerada com sucesso!');
            } else {
                const errData = await response.json();
                showExportMessage(errData.message || 'Erro ao gerar planilha.', false);
            }
        } catch (err) {
            console.error('Erro ao gerar planilha:', err);
            showExportMessage('Erro de conexão.', false);
        }
    });

    // Carrega pedidos automaticamente ao entrar na página
    if (window.location.pathname === '/exportar') loadPedidos();
});

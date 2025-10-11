const userId = localStorage.getItem("userId");

document.addEventListener("DOMContentLoaded", async () => {
    const tbody = document.getElementById('pedidosTableBody');
    const mensagemErro = document.getElementById("mensagemErro");

    try {
        const response = await fetch("/api/pedidos", {
            headers: {
                "Content-Type": "application/json",
                "X-User-Id": userId
            }
        });

        if (!response.ok) {
            throw new Error(`Erro na resposta da API: ${response.status}`);
        }

        const pedidos = await response.json();

        // Se não houver pedidos
        if (pedidos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10">Nenhum pedido encontrado.</td></tr>`;
            return;
        }

        // Limpa o tbody antes de preencher
        tbody.innerHTML = "";

        pedidos.forEach(pedido => {
            const statusCapitalizado = pedido.status.charAt(0).toUpperCase() + pedido.status.slice(1);
            const prioridadeCapitalizada = pedido.prioridade.charAt(0).toUpperCase() + pedido.prioridade.slice(1);
            const responsavel = pedido.responsavel || "Damaris";

            const row = `
                <tr>
                    <td>${pedido.id}</td>
                    <td>${pedido.clienteNome}</td>
                    <td>${pedido.dataEvento}</td>
                    <td>${pedido.dataRetirada}</td>
                    <td>${pedido.horarioRetirada}</td>
                    <td>${pedido.tipoPedido}</td>
                    <td>${pedido.quantidade}</td>
                    <td>${statusCapitalizado}</td>
                    <td>${prioridadeCapitalizada}</td>
                    <td>${responsavel}</td>
                </tr>
            `;
            tbody.insertAdjacentHTML("beforeend", row);
        });

    } catch (error) {
        console.error("Erro ao carregar pedidos:", error);
        mensagemErro.style.display = "block";
    }
});

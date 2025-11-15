// reports.js

// ==========================
// 1️⃣ CAPTURA DE DADOS FLASK
// ==========================
// Esses blocos de <script type="application/json"> estarão no HTML.
// Aqui fazemos a leitura deles e convertemos para objetos JS.
const pedidosMensais = JSON.parse(document.getElementById('data-pedidos').textContent);
const categorias = JSON.parse(document.getElementById('data-categorias').textContent);
const topClientes = JSON.parse(document.getElementById('data-clientes').textContent);
const comparativo = JSON.parse(document.getElementById('data-comparativo').textContent);

// ==========================
// 2️⃣ GRÁFICO: EVOLUÇÃO DE PEDIDOS
// ==========================
const pedidosCtx = document.getElementById('pedidosChart').getContext('2d');
new Chart(pedidosCtx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        datasets: [{
            label: 'Pedidos',
            data: pedidosMensais,
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } }
    }
});

// ==========================
// 3️⃣ GRÁFICO: PRODUTOS POR CATEGORIA
// ==========================
const categoriasCtx = document.getElementById('categoriasChart').getContext('2d');
new Chart(categoriasCtx, {
    type: 'doughnut',
    data: {
        labels: Object.keys(categorias),
        datasets: [{
            data: Object.values(categorias),
            backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b']
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true
    }
});

// ==========================
// 4️⃣ GRÁFICO: TOP 5 CLIENTES
// ==========================
const clientesCtx = document.getElementById('clientesChart').getContext('2d');
new Chart(clientesCtx, {
    type: 'bar',
    data: {
        labels: Object.keys(topClientes),
        datasets: [{
            label: 'Pedidos',
            data: Object.values(topClientes),
            backgroundColor: '#6366f1'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } }
    }
});

// ==========================
// 5️⃣ GRÁFICO: COMPARATIVO ANO A ANO
// ==========================
const comparativoCtx = document.getElementById('comparativoChart').getContext('2d');
new Chart(comparativoCtx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        datasets: [
            {
                label: '2025',
                data: comparativo["2025"],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)'
            },
            {
                label: '2024',
                data: comparativo["2024"],
                borderColor: '#94a3b8',
                backgroundColor: 'rgba(148, 163, 184, 0.1)'
            },
            {
                label: '2023',
                data: comparativo["2023"],
                borderColor: '#43c3ffff',
                backgroundColor: 'rgba(93, 201, 21, 0.1)'
            },
            {
                label: '2022',
                data: comparativo["2022"],
                borderColor: '#f720ecff',
                backgroundColor: 'rgba(125, 7, 204, 0.1)'
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true
    }
});

// ==========================
// ⚙️ FUTUROS RECURSOS
// ==========================
// Aqui no futuro você poderá implementar:
// - Filtros dinâmicos (por período, cliente, produto);
// - Atualização dos gráficos via fetch() sem recarregar a página;
// - Ações dos botões “Exportar Excel/PDF”.

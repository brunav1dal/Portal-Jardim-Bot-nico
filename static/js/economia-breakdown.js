/* Objetivo: ilustrar a divisão do valor original da energia solar no modal de economia real. */
(() => {
  let chart = null;

  // Remove a instância anterior para permitir abrir outros indicadores e voltar ao gráfico.
  function destroy() {
    if (chart) { chart.destroy(); chart = null; }
    document.getElementById('economiaPartition').hidden = true;
  }

  // As parcelas são uma referência percentual, não valores adicionais ao histórico do período.
  function render(enabled) {
    destroy();
    if (!enabled) return;
    const section = document.getElementById('economiaPartition');
    section.hidden = false;
    if (typeof Chart === 'undefined') return;

    // A base é o valor original: 50% não são pagos, 25% retornam em moeda social e 25% ficam no banco.
    chart = new Chart(document.getElementById('economiaPartitionChart'), {
      type: 'doughnut',
      data: {
        labels: ['Economia na energia', 'Cashback em Orquídeas', 'Banco após o cashback'],
        datasets: [{
          data: [50, 25, 25],
          backgroundColor: ['#15803d', '#d97706', '#7c3aed'],
          borderColor: '#ffffff', borderWidth: 3, hoverOffset: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '68%',
        animation: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 450 },
        plugins: {
          // A legenda HTML ao lado permanece legível mesmo sem canvas e é acessível a leitores de tela.
          legend: { display: false },
          tooltip: { callbacks: { label: item => `${item.label}: ${item.raw}% do valor original` } }
        }
      }
    });
  }

  // O modal compartilhado chama este módulo apenas para indicadores que habilitam a composição.
  window.EconomiaBreakdown = { render, destroy };
})();

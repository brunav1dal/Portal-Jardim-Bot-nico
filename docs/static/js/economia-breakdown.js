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

    // As três parcelas compõem uma única barra de 100%; o cashback integra os 50% pagos ao banco.
    chart = new Chart(document.getElementById('economiaPartitionChart'), {
      type: 'bar',
      data: {
        labels: ['Valor original da energia'],
        datasets: [
          { label: 'Economia direta', data: [50], backgroundColor: '#15803d' },
          { label: 'Retorno em Orquídeas', data: [25], backgroundColor: '#86efac' },
          { label: 'Custo efetivo da energia', data: [25], backgroundColor: '#dc2626' }
        ].map(dataset => ({ ...dataset, borderWidth: 0, barThickness: 36 }))
      },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        animation: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 450 },
        scales: {
          x: { stacked: true, min: 0, max: 100, border: { display: false }, grid: { display: false }, ticks: { stepSize: 25, callback: value => `${value}%`, color: '#64748b', font: { size: 10 } } },
          y: { stacked: true, display: false }
        },
        plugins: {
          // A legenda HTML ao lado permanece legível mesmo sem canvas e é acessível a leitores de tela.
          legend: { display: false },
          tooltip: { callbacks: { label: item => `${item.dataset.label}: ${item.raw}% do valor original` } }
        }
      },
      // Identifica cada segmento dentro da barra, mantendo a legenda HTML como alternativa acessível.
      plugins: [{
        id: 'economyPartitionLabels',
        afterDatasetsDraw(chart) {
          const { ctx } = chart;
          ctx.save(); ctx.fillStyle = '#ffffff'; ctx.font = '600 12px system-ui';
          ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          chart.data.datasets.forEach((dataset, index) => {
            const bar = chart.getDatasetMeta(index).data[0];
            ctx.fillStyle = index === 1 ? '#14532d' : '#ffffff';
            if (bar && Math.abs(bar.x - bar.base) >= 38) ctx.fillText(`${dataset.data[0]}%`, (bar.x + bar.base) / 2, bar.y);
          });
          ctx.restore();
        }
      }]
    });
  }

  // O modal compartilhado chama este módulo apenas para indicadores que habilitam a composição.
  window.EconomiaBreakdown = { render, destroy };
})();

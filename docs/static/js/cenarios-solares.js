(() => {
  const explanations = {
    cota: ['O que é cota solar?', 'É a quantidade de energia solar destinada ao beneficiário no mês, medida em kWh. Neste esquema ilustrativo, a cota é de 120 kWh. O uso depende do consumo elegível; kWh é uma medida de energia, não um valor em reais.'],
    social: ['O que é tarifa social?', 'É um benefício aplicado à conta de energia de famílias elegíveis. Neste esquema, a faixa ilustrada é de até 80 kWh. Ela é diferente da cota solar: a faixa atendida pela tarifa social não é novamente atendida pela cota. A situação real depende do cadastro e da fatura da concessionária.'],
    excedente: ['O que é excedente?', 'É a parte do consumo que fica além da energia atendida pelos benefícios do exemplo. No cenário 2: 250 − 80 − 120 = 50 kWh. No cenário 4: 180 − 120 = 60 kWh. Essa parte permanece na conta da concessionária.'],
    saldo: ['O que é cota não utilizada?', 'É a parte da cota solar que não foi usada no mês. Com cota de 120 kWh e uso solar de 100 kWh, sobram 20 kWh. No primeiro cenário, sem uso solar, os 120 kWh da cota ficam disponíveis como crédito de energia para uso futuro, conforme as regras do programa. Crédito de energia é medido em kWh, não em reais.'],
    orquideas: ['O que são Orquídeas?', 'Orquídea é a moeda social do Banco Comunitário Jardim Botânico. O primeiro cenário apresenta uma recompensa ilustrativa de 5 Orquídeas. O valor efetivo depende das regras do programa.']
  };
  const dialog = document.getElementById('solarExplanation');
  if (!dialog) return;
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('scenario-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    document.querySelectorAll('.scenario-card').forEach(card => observer.observe(card));
  }
  document.querySelectorAll('[data-solar-topic]').forEach(button => {
    button.addEventListener('click', () => {
      const [title, description] = explanations[button.dataset.solarTopic];
      document.getElementById('solarExplanationTitle').textContent = title;
      document.getElementById('solarExplanationText').textContent = description;
      dialog.showModal();
    });
  });
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) {
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  } });
})();

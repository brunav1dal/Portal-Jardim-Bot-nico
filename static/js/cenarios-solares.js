(() => {
  const explanations = {
    cota: ['O que é cota solar?', 'É a quantidade de energia solar destinada ao beneficiário no mês, medida em kWh. Neste esquema ilustrativo, a cota é de 120 kWh. O uso depende do consumo elegível; kWh é uma medida de energia, não um valor em reais.'],
    social: ['O que é tarifa social?', 'É um benefício aplicado à conta de energia de famílias elegíveis. Neste esquema, a faixa ilustrada é de até 80 kWh. Ela é diferente da cota solar: a faixa atendida pela tarifa social não é novamente atendida pela cota. A situação real depende do cadastro e da fatura da concessionária.'],
    excedente: ['O que é excedente?', 'É a parte do consumo que fica além da energia atendida pelos benefícios do exemplo. No cenário 2: 250 − 80 − 120 = 50 kWh. No cenário 4: 180 − 120 = 60 kWh. Essa parte permanece na conta da concessionária.'],
    saldo: ['O que é cota não utilizada?', 'É a parte da cota solar que não foi usada no mês. Com cota de 120 kWh e uso solar de 100 kWh, sobram 20 kWh. No cenário 1, sem uso solar, a cota não utilizada é de 120 kWh: os 50 kWh escritos na imagem não representam esse saldo. Crédito de energia não é dinheiro.'],
    orquideas: ['O que são Orquídeas?', 'Orquídea é a moeda social do Banco Comunitário Jardim Botânico. A imagem apresenta uma recompensa ilustrativa de 5 Orquídeas no primeiro cenário. O valor efetivo depende das regras do programa.']
  };
  const dialog = document.getElementById('solarExplanation');
  if (!dialog) return;
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

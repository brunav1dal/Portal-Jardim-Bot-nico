(() => {
  const explanations = {
    nao_utilizado: ['O que significa o cinza?', 'O cinza mostra um benefício disponível que não foi utilizado. No primeiro cenário: 10 kWh da faixa de isenção e 120 kWh da cota solar. No terceiro: 20 kWh da cota solar. Isenção não utilizada não é crédito solar; o saldo da cota solar segue as regras do programa. Os trechos cinza não entram no consumo indicado no card.'],
    isencao_saldo: ['Isenção não utilizada: 10 kWh', 'Neste exemplo, a faixa de isenção é de 80 kWh e o consumo é de 70 kWh. Por isso, 70 kWh aparecem em verde e os 10 kWh restantes aparecem em cinza. Esses 10 kWh não foram consumidos: não são cobrança, energia solar ou crédito solar acumulado. Nos cenários sem tarifa social, essa faixa de isenção não se aplica.'],
    cota: ['Cota do painel solar comunitário', 'É a energia fornecida pelo painel solar comunitário e destinada ao beneficiário no mês. Nestes exemplos, a cota é de 120 kWh. A energia solar utilizada custa metade da tarifa por kWh equivalente da concessionária de energia elétrica. O valor depende da quantidade de energia solar efetivamente utilizada.'],
    preco: ['Quanto custa a energia da cota?', 'A tarifa da energia fornecida pelo painel solar comunitário é 50% da tarifa por kWh equivalente da concessionária de energia elétrica. Exemplo hipotético: se a tarifa equivalente é R$ 1,00/kWh, a energia solar custa R$ 0,50/kWh. Usar 120 kWh solares custaria R$ 60,00, em vez de R$ 120,00 pela mesma quantidade de energia. Essa comparação é da energia: não significa reduzir pela metade toda a fatura, que pode incluir excedente, impostos e outros encargos.'],
    social: ['O que é tarifa social?', 'É um benefício aplicado à conta de energia de famílias elegíveis. Neste esquema, a faixa ilustrada é de até 80 kWh. Ela é diferente da cota solar: a faixa atendida pela tarifa social não é novamente atendida pela cota. A situação real depende do cadastro e da fatura da concessionária de energia elétrica.'],
    excedente: ['O que é excedente?', 'É a parte do consumo que fica além da energia atendida pelos benefícios do exemplo. No cenário 2: 250 − 80 − 120 = 50 kWh. No cenário 4: 180 − 120 = 60 kWh. Essa parte permanece na conta da concessionária de energia elétrica.'],
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

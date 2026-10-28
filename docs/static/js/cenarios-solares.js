(() => {
  const explanations = {
    nao_utilizado: ['O que significa o cinza?', 'O cinza mostra um benefício disponível que não foi utilizado. No primeiro cenário: 10 kWh da faixa de isenção e 120 kWh da cota solar solidária. No terceiro: 20 kWh da cota solar solidária. Isenção não utilizada não é crédito solar; o saldo da cota solar solidária segue as regras do programa. Os trechos cinza não entram no consumo indicado no card.'],
    isencao_saldo: ['Isenção não utilizada: 10 kWh', 'Neste exemplo, a faixa de isenção é de 80 kWh e o consumo é de 70 kWh. Por isso, 70 kWh aparecem em verde e os 10 kWh restantes aparecem em cinza. Esses 10 kWh não foram consumidos: não são cobrança, energia solar ou crédito solar acumulado. Nos cenários sem tarifa social, essa faixa de isenção não se aplica.'],
    cota: ['Cota solar solidária do painel comunitário', 'É a energia fornecida pelo painel solar comunitário e destinada ao beneficiário no mês. Nestes exemplos, a cota é de 120 kWh. A energia solar utilizada custa metade da tarifa por kWh equivalente da concessionária de energia elétrica. O valor depende da quantidade de energia solar efetivamente utilizada.'],
    preco: ['Quanto custa a energia da cota?', 'A tarifa da energia fornecida pelo painel solar comunitário é 50% da tarifa por kWh equivalente da concessionária de energia elétrica. Exemplo hipotético: se a tarifa equivalente é R$ 1,00/kWh, a energia solar custa R$ 0,50/kWh. Usar 120 kWh solares custaria R$ 60,00, em vez de R$ 120,00 pela mesma quantidade de energia. Essa comparação é da energia: não significa reduzir pela metade toda a fatura, que pode incluir excedente, impostos e outros encargos.'],
    social: ['Tarifa Social: benefício governamental', 'É um benefício governamental para famílias de baixa renda que atendem aos requisitos da Tarifa Social de Energia Elétrica. A parcela de consumo até 80 kWh por mês tem desconto de 100% na tarifa de energia; a parcela acima disso não recebe esse desconto. Base legal: art. 1º, incisos I e II, da Lei nº 12.212/2010, com redação dada pelo art. 3º da Lei nº 15.235/2025. A isenção não é fornecida pelo projeto solar solidário. Impostos, iluminação pública e outros encargos podem permanecer na fatura.'],
    excedente: ['Excedente: energia da concessionária', 'Quando a cota solar solidária não é suficiente para atender ao consumo restante, a pessoa usa energia da própria concessionária de energia elétrica. Essa parte é o excedente, cobrado pela concessionária. No cenário 2, após 80 kWh de isenção e 120 kWh solidários, faltam 50 kWh. No cenário 4, após 120 kWh solidários, faltam 60 kWh.'],
    saldo: ['Saldo de energia solar solidária', 'É a energia da cota solar solidária que permanece disponível conforme as regras do programa. Com cota de 120 kWh e uso de 100 kWh, o saldo é de 20 kWh. No primeiro cenário, a tarifa social atende ao consumo de 70 kWh e os 120 kWh solidários permanecem como saldo. Esse saldo é medido em kWh, não em reais, e é diferente da faixa de isenção governamental.'],
    orquideas: ['5 Orquídeas no programa Orquídea Solar', 'Orquídea é a moeda social do Banco Comunitário Jardim Botânico. No programa Orquídea Solar, a pessoa ganha 5 Orquídeas na situação do primeiro cenário: seu consumo de 70 kWh está dentro da faixa de isenção de até 80 kWh da Tarifa Social. Nesse cenário, ela recebe as 5 Orquídeas mesmo sem precisar usar a cota solar solidária para atender ao consumo do mês.']
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
      const source = document.getElementById('solarExplanationSource');
      if (source) source.hidden = button.dataset.solarTopic !== 'social';
      dialog.showModal();
    });
  });
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) {
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  } });
})();

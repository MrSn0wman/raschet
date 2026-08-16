/* =========================================================
   РАСЧЁТ.РФ — библиотека формул калькуляторов
   Чистые функции: не трогают DOM, легко тестируются
   ========================================================= */

const Calc = {

  // ---------- Площадь ----------
  areaRectangle(a, b){ return a * b; },
  areaCircle(r){ return Math.PI * r * r; },
  areaTriangle(base, height){ return (base * height) / 2; },

  // ---------- Объём ----------
  volumeBox(a, b, c){ return a * b * c; },
  volumeCylinder(r, h){ return Math.PI * r * r * h; },
  volumeSphere(r){ return (4 / 3) * Math.PI * r ** 3; },

  // ---------- Проценты ----------
  percentOfNumber(percent, number){ return (percent / 100) * number; },
  numberIsWhatPercentOf(part, whole){ return (part / whole) * 100; },
  percentChange(oldValue, newValue){ return ((newValue - oldValue) / oldValue) * 100; },

  // ---------- ИМТ ----------
  bmi(weightKg, heightCm){
    const h = heightCm / 100;
    return weightKg / (h * h);
  },
  bmiCategory(bmiValue){
    if (bmiValue < 16) return 'Выраженный дефицит массы тела';
    if (bmiValue < 18.5) return 'Недостаточная масса тела';
    if (bmiValue < 25) return 'Норма';
    if (bmiValue < 30) return 'Избыточная масса тела';
    if (bmiValue < 35) return 'Ожирение I степени';
    if (bmiValue < 40) return 'Ожирение II степени';
    return 'Ожирение III степени';
  },

  /**
   * Аннуитетный платёж по кредиту/ипотеке.
   * principal — сумма кредита, annualRatePercent — ставка годовых,
   * months — срок в месяцах
   * Возвращает { monthlyPayment, totalPayment, totalInterest, schedule }
   */
  annuityLoan(principal, annualRatePercent, months){
    const i = (annualRatePercent / 100) / 12;
    let monthlyPayment;
    if (i === 0){
      monthlyPayment = principal / months;
    } else {
      const factor = Math.pow(1 + i, months);
      monthlyPayment = principal * (i * factor) / (factor - 1);
    }
    const totalPayment = monthlyPayment * months;
    const totalInterest = totalPayment - principal;

    // график первых N платежей (для проверки/детализации), полностью — по запросу
    const schedule = [];
    let balance = principal;
    for (let m = 1; m <= months; m++){
      const interestPart = i === 0 ? 0 : balance * i;
      const principalPart = monthlyPayment - interestPart;
      balance -= principalPart;
      schedule.push({
        month: m,
        payment: monthlyPayment,
        interest: interestPart,
        principal: principalPart,
        balance: Math.max(balance, 0)
      });
    }

    return {
      monthlyPayment,
      totalPayment,
      totalInterest,
      schedule
    };
  },

  /**
   * Вклад с капитализацией процентов (ежемесячная капитализация)
   * principal — сумма вклада, annualRatePercent — ставка годовых,
   * months — срок в месяцах, monthlyTopUp — пополнение в месяц (0 если нет)
   */
  depositWithCapitalization(principal, annualRatePercent, months, monthlyTopUp = 0){
    const i = (annualRatePercent / 100) / 12;
    let balance = principal;
    let totalTopUp = 0;
    for (let m = 1; m <= months; m++){
      balance += balance * i;
      balance += monthlyTopUp;
      totalTopUp += monthlyTopUp;
    }
    const totalInterest = balance - principal - totalTopUp;
    return {
      finalBalance: balance,
      totalInterest,
      totalTopUp
    };
  },

  /**
   * Простой вклад без капитализации (проценты выплачиваются, не прибавляются к телу)
   */
  depositSimple(principal, annualRatePercent, months){
    const totalInterest = principal * (annualRatePercent / 100) * (months / 12);
    return {
      finalBalance: principal + totalInterest,
      totalInterest
    };
  }
};

if (typeof module !== 'undefined' && module.exports){
  module.exports = Calc;
}

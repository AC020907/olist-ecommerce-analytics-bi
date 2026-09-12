-- Business question: ¿Qué métodos de pago predominan?
-- Real result: credit_card dominates both volume (76,795 payments) and
-- value (R$12.54M, 78.3% of total payment value) and is the only
-- method used with real installment plans (avg 3.51); the rest average
-- ~1.00 installments.
SELECT * FROM reporting.vw_payment_method_summary;

-- Installments distribution for credit card specifically.
SELECT payment_installments, COUNT(*) AS payments
FROM analytics.fact_payments
WHERE payment_type = 'credit_card'
GROUP BY payment_installments
ORDER BY payment_installments;

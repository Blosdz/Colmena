"""Regresión logística (harness §21, Fase 9). Función pura vía numpy (IRLS).

No se usa scikit-learn para evitar añadir una dependencia pesada nueva en
esta fase — IRLS (Newton-Raphson reponderado) converge en pocas iteraciones
para problemas pequeños/medianos, que es el caso de uso de Colmena.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def compute_logistic_regression(
    predictors: list[list[float]], outcome: list[int], max_iter: int = 50, tol: float = 1e-8
) -> dict:
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(outcome, dtype=float)
    n, p = x.shape
    x_design = np.column_stack([np.ones(n), x])  # intercepto + predictores

    beta = np.zeros(x_design.shape[1])
    for _ in range(max_iter):
        linear = x_design @ beta
        probs = 1 / (1 + np.exp(-linear))
        probs = np.clip(probs, 1e-10, 1 - 1e-10)
        weights = probs * (1 - probs)

        gradient = x_design.T @ (y - probs)
        hessian = (x_design * weights[:, None]).T @ x_design
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            break
        beta_new = beta + step
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        beta = beta_new

    linear = x_design @ beta
    probs = np.clip(1 / (1 + np.exp(-linear)), 1e-10, 1 - 1e-10)
    weights = probs * (1 - probs)
    hessian = (x_design * weights[:, None]).T @ x_design

    try:
        cov = np.linalg.inv(hessian)
        standard_errors = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        standard_errors = np.full(beta.shape, np.nan)

    z_scores = beta / standard_errors
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z_scores)))

    log_likelihood = float(np.sum(y * np.log(probs) + (1 - y) * np.log(1 - probs)))
    base_rate = float(np.mean(y))
    base_rate = min(max(base_rate, 1e-10), 1 - 1e-10)
    null_log_likelihood = float(n * (base_rate * np.log(base_rate) + (1 - base_rate) * np.log(1 - base_rate)))
    pseudo_r2 = 1 - (log_likelihood / null_log_likelihood) if null_log_likelihood != 0 else None

    predicted = (probs >= 0.5).astype(int)
    accuracy = float(np.mean(predicted == y))

    return {
        "n": n,
        "intercept": float(beta[0]),
        "coefficients": [float(b) for b in beta[1:]],
        "odds_ratios": [float(np.exp(b)) for b in beta[1:]],
        "standard_errors": [float(s) for s in standard_errors[1:]],
        "p_values": [float(pv) for pv in p_values[1:]],
        "pseudo_r_squared": pseudo_r2,
        "log_likelihood": log_likelihood,
        "accuracy": accuracy,
    }

from plyer import notification

notification.notify(
    title="Aviso do Python",
    message="Esta notificação funciona em múltiplos sistemas operacionais.",
    app_name="Meu App",
    timeout=5 # Tempo em segundos que a notificação fica ativa
)
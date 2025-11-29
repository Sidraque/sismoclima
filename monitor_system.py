from app import create_app
from app.models import User, AlertLog
from datetime import datetime, timedelta
from tabulate import tabulate
import os


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print("=" * 70)
    print("🌍 SISMOCLIMA - DASHBOARD ADMINISTRATIVO".center(70))
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")


def get_user_statistics():
    total_users = User.query.count()
    confirmed_users = User.query.filter_by(confirmed=True).count()
    active_users = User.query.filter_by(active=True, confirmed=True).count()
    pending_users = User.query.filter_by(confirmed=False).count()
    
    return {
        'total': total_users,
        'confirmed': confirmed_users,
        'active': active_users,
        'pending': pending_users,
        'inactive': confirmed_users - active_users
    }


def get_alert_statistics(hours=24):
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    total_alerts = AlertLog.query.filter(AlertLog.sent_at >= time_threshold).count()
    successful_alerts = AlertLog.query.filter(
        AlertLog.sent_at >= time_threshold,
        AlertLog.success == True
    ).count()
    failed_alerts = AlertLog.query.filter(
        AlertLog.sent_at >= time_threshold,
        AlertLog.success == False
    ).count()
    
    earthquake_alerts = AlertLog.query.filter(
        AlertLog.sent_at >= time_threshold,
        AlertLog.alert_type == 'earthquake'
    ).count()
    weather_alerts = AlertLog.query.filter(
        AlertLog.sent_at >= time_threshold,
        AlertLog.alert_type == 'weather'
    ).count()
    
    return {
        'total': total_alerts,
        'successful': successful_alerts,
        'failed': failed_alerts,
        'earthquake': earthquake_alerts,
        'weather': weather_alerts,
        'success_rate': (successful_alerts / total_alerts * 100) if total_alerts > 0 else 0
    }


def get_recent_users(limit=10):
    """Retorna usuários recentes"""
    return User.query.order_by(User.created_at.desc()).limit(limit).all()


def get_recent_alerts(limit=10):
    """Retorna alertas recentes"""
    return AlertLog.query.order_by(AlertLog.sent_at.desc()).limit(limit).all()


def get_cities_ranking():
    """Retorna ranking de cidades com mais usuários"""
    from sqlalchemy import func
    
    cities = db.session.query(
        User.city,
        func.count(User.id).label('count')
    ).filter_by(
        confirmed=True,
        active=True
    ).group_by(
        User.city
    ).order_by(
        func.count(User.id).desc()
    ).limit(10).all()
    
    return cities


def display_user_statistics():
    """Exibe estatísticas de usuários"""
    stats = get_user_statistics()
    
    print("👥 ESTATÍSTICAS DE USUÁRIOS")
    print("-" * 70)
    print(f"  Total de cadastros:        {stats['total']}")
    print(f"  Cadastros confirmados:     {stats['confirmed']} ({stats['confirmed']/max(stats['total'],1)*100:.1f}%)")
    print(f"  Usuários ativos:           {stats['active']} ({stats['active']/max(stats['confirmed'],1)*100:.1f}%)")
    print(f"  Usuários inativos:         {stats['inactive']}")
    print(f"  Aguardando confirmação:    {stats['pending']}")
    print()


def display_alert_statistics():
    """Exibe estatísticas de alertas"""
    stats_24h = get_alert_statistics(hours=24)
    stats_7d = get_alert_statistics(hours=168)
    
    print("🚨 ESTATÍSTICAS DE ALERTAS")
    print("-" * 70)
    
    print("  📊 Últimas 24 horas:")
    print(f"    Total de alertas:        {stats_24h['total']}")
    print(f"    Alertas sísmicos:        {stats_24h['earthquake']}")
    print(f"    Alertas meteorológicos:  {stats_24h['weather']}")
    print(f"    Enviados com sucesso:    {stats_24h['successful']}")
    print(f"    Falhas no envio:         {stats_24h['failed']}")
    print(f"    Taxa de sucesso:         {stats_24h['success_rate']:.1f}%")
    
    print("\n  📊 Últimos 7 dias:")
    print(f"    Total de alertas:        {stats_7d['total']}")
    print(f"    Taxa de sucesso:         {stats_7d['success_rate']:.1f}%")
    print()


def display_recent_users():
    """Exibe usuários recentes"""
    users = get_recent_users(limit=10)
    
    print("📝 CADASTROS RECENTES (Últimos 10)")
    print("-" * 70)
    
    if not users:
        print("  Nenhum usuário cadastrado ainda.")
    else:
        table_data = []
        for user in users:
            status = "✅" if user.confirmed else "⏳"
            active = "🟢" if user.active else "🔴"
            table_data.append([
                status,
                active,
                user.name[:25],
                user.city,
                user.created_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        headers = ["Status", "Ativo", "Nome", "Cidade", "Cadastro"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
    print()


def display_recent_alerts():
    """Exibe alertas recentes"""
    alerts = get_recent_alerts(limit=10)
    
    print("📬 ALERTAS RECENTES (Últimos 10)")
    print("-" * 70)
    
    if not alerts:
        print("  Nenhum alerta enviado ainda.")
    else:
        table_data = []
        for alert in alerts:
            status = "✅" if alert.success else "❌"
            tipo_icon = "🌍" if alert.alert_type == 'earthquake' else "☁️"
            user_name = alert.user.name if alert.user else "N/A"
            
            table_data.append([
                status,
                tipo_icon,
                alert.alert_type.capitalize(),
                user_name[:20],
                alert.sent_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        headers = ["Status", "Tipo", "Categoria", "Usuário", "Enviado em"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
    print()


def display_cities_ranking():
    """Exibe ranking de cidades"""
    cities = get_cities_ranking()
    
    print("🏙️ TOP CIDADES (Usuários ativos)")
    print("-" * 70)
    
    if not cities:
        print("  Nenhuma cidade com usuários ativos.")
    else:
        table_data = []
        for i, (city, count) in enumerate(cities, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
            table_data.append([medal, city, count])
        
        headers = ["Rank", "Cidade", "Usuários"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
    print()


def display_system_health():
    """Exibe saúde do sistema"""
    print("💚 SAÚDE DO SISTEMA")
    print("-" * 70)
    
    # Verificar conexão com banco
    try:
        User.query.first()
        db_status = "✅ Conectado"
    except Exception as e:
        db_status = f"❌ Erro: {str(e)[:40]}"
    
    print(f"  Banco de dados:  {db_status}")
    
    # Verificar ambiente
    from config.settings import Config
    
    api_status = []
    if Config.OPENWEATHER_API_KEY:
        api_status.append("✅ OpenWeather")
    else:
        api_status.append("❌ OpenWeather")
    
    if Config.CALLMEBOT_API_KEY:
        api_status.append("✅ CallMeBot")
    else:
        api_status.append("❌ CallMeBot")
    
    print(f"  APIs configuradas: {' | '.join(api_status)}")
    print(f"  Intervalo terremoto: {Config.EARTHQUAKE_CHECK_INTERVAL} min")
    print(f"  Intervalo clima: {Config.WEATHER_CHECK_INTERVAL} min")
    print()


def main():
    """Função principal"""
    app = create_app()
    
    with app.app_context():
        # Importar db após criar app
        global db
        from app import db
        
        while True:
            clear_screen()
            print_header()
            
            display_system_health()
            display_user_statistics()
            display_alert_statistics()
            display_recent_users()
            display_recent_alerts()
            display_cities_ranking()
            
            print("=" * 70)
            print("Opções: [R]efresh | [E]xportar Relatório | [S]air")
            print("=" * 70)
            
            choice = input("\nEscolha uma opção: ").lower()
            
            if choice == 's':
                print("\n👋 Encerrando dashboard...")
                break
            elif choice == 'e':
                export_report()
                input("\nPressione ENTER para continuar...")
            elif choice == 'r':
                continue
            else:
                continue


def export_report():
    """Exporta relatório em formato texto"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"relatorio_sismoclima_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("RELATÓRIO SISMOCLIMA\n")
        f.write("=" * 70 + "\n")
        f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        # Estatísticas
        stats = get_user_statistics()
        f.write("USUÁRIOS:\n")
        f.write(f"  Total: {stats['total']}\n")
        f.write(f"  Ativos: {stats['active']}\n")
        f.write(f"  Pendentes: {stats['pending']}\n\n")
        
        alert_stats = get_alert_statistics(hours=168)
        f.write("ALERTAS (7 dias):\n")
        f.write(f"  Total: {alert_stats['total']}\n")
        f.write(f"  Sucesso: {alert_stats['successful']}\n")
        f.write(f"  Falhas: {alert_stats['failed']}\n")
        f.write(f"  Taxa de sucesso: {alert_stats['success_rate']:.1f}%\n")
    
    print(f"\n✅ Relatório exportado: {filename}")


if __name__ == '__main__':
    # Verificar se tabulate está instalado
    try:
        from tabulate import tabulate
    except ImportError:
        print("⚠️ Instalando dependência 'tabulate'...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'tabulate'])
        from tabulate import tabulate
    
    main()
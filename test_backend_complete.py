"""
Test complet du backend - Vérification que tout fonctionne

Ce fichier regroupe tous les tests du backend:
- Santé de l'API
- Endpoints API
- Création de session
- Tous les agents (FAQ, Order, Sentiment, Escalation)
- Création de tickets avec session_id
- Persistance des données
"""
import requests
import json
import time
import sys
import io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_api_health():
    """Test 1: Vérification de l'API"""
    print_section("TEST 1: Santé de l'API")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API est disponible")
            print(f"   Status: {data.get('status')}")
            print(f"   Metrics: {data.get('metrics', {})}")
            return True
        else:
            print(f"❌ API retourne erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_all_endpoints():
    """Test 2: Tous les endpoints"""
    print_section("TEST 2: Endpoints API")
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/metrics", None),
        ("GET", "/analytics", None),
        ("GET", "/orders", None),
        ("GET", "/tickets", None),
    ]
    
    all_ok = True
    for method, endpoint, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {method} {endpoint}")
            else:
                print(f"   ⚠️  {method} {endpoint} - Status: {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ {method} {endpoint} - Erreur: {e}")
            all_ok = False
    
    return all_ok

def test_session_creation():
    """Test 3: Création de session"""
    print_section("TEST 3: Création de session")
    try:
        response = requests.post(
            f"{API_BASE_URL}/sessions/create",
            json={"user_id": f"test_backend_{int(time.time())}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ Session créée: {session_id}")
            return session_id, data.get('user_id', 'test_user')
        else:
            print(f"❌ Erreur création session: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, None

def test_all_agents(session_id, user_id):
    """Test 4: Tous les agents"""
    print_section("TEST 4: Tous les agents")
    
    tests = [
        ("FAQ Agent", "Quelle est votre politique de retour?"),
        ("Order Agent", "Je veux suivre ma commande 11111"),
        ("Sentiment Agent", "Je suis très frustré"),
        ("Escalation Agent", "Créez un ticket pour mon problème urgent")
    ]
    
    all_ok = True
    for agent_name, message in tests:
        print(f"\n   🔍 Test {agent_name}: {message[:50]}...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": message,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                if response_text and len(response_text) > 20:
                    print(f"      ✅ Réponse reçue ({len(response_text)} caractères)")
                else:
                    print(f"      ⚠️  Réponse trop courte")
                    all_ok = False
            else:
                print(f"      ❌ Erreur: {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            all_ok = False
        
        time.sleep(1)
    
    return all_ok

def test_ticket_creation(session_id, user_id):
    """Test 5: Création de ticket avec session_id"""
    print_section("TEST 5: Création de ticket avec session_id")
    
    # Envoyer plusieurs messages pour établir une conversation
    messages = [
        "Bonjour",
        "J'ai un problème urgent avec mon produit",
        "Mon produit est complètement cassé. Créez un ticket maintenant s'il vous plaît."
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n   💬 Message {i}: {msg[:60]}...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": msg,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                resp_text = data.get('response', '')
                print(f"      ✅ Réponse: {resp_text[:80]}...")
                
                # Vérifier si ticket mentionné
                if 'TICKET-' in resp_text.upper():
                    print(f"      🎫 Ticket mentionné dans la réponse!")
            else:
                print(f"      ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Erreur: {e}")
        
        time.sleep(2)
    
    # Attendre que tout soit sauvegardé
    print("\n   ⏳ Attente de 5 secondes...")
    time.sleep(5)
    
    # Vérifier les tickets
    print("\n   🎫 Vérification des tickets...")
    try:
        tickets_response = requests.get(f"{API_BASE_URL}/tickets", timeout=5)
        if tickets_response.status_code == 200:
            tickets_data = tickets_response.json()
            tickets = tickets_data.get('tickets', [])
            
            # Chercher par session_id
            found_tickets = [t for t in tickets if t.get('session_id') == session_id]
            
            if found_tickets:
                print(f"      ✅ {len(found_tickets)} ticket(s) trouvé(s) avec session_id!")
                for ticket in found_tickets:
                    print(f"         - {ticket.get('ticket_id')}: session={ticket.get('session_id')}, user={ticket.get('user_id')}")
                return True
            else:
                print(f"      ⚠️  Aucun ticket trouvé pour session {session_id}")
                
                # Vérifier le fichier JSON directement
                try:
                    with open("data/tickets.json", "r", encoding="utf-8") as f:
                        tickets_json = json.load(f)
                        
                        # Chercher les tickets récents
                        now = datetime.now()
                        recent_tickets = []
                        for ticket_id, ticket_data in tickets_json.items():
                            created_str = ticket_data.get('created_at', '')
                            if created_str:
                                try:
                                    created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                                    if (now - created.replace(tzinfo=None)).total_seconds() < 300:
                                        recent_tickets.append((ticket_id, ticket_data))
                                except:
                                    pass
                        
                        if recent_tickets:
                            print(f"      📋 Tickets créés récemment: {len(recent_tickets)}")
                            for ticket_id, ticket_data in recent_tickets[-3:]:
                                has_session = ticket_data.get('session_id') not in [None, 'N/A', '']
                                has_user = ticket_data.get('user_id') not in [None, 'N/A', '']
                                status = "✅" if (has_session and has_user) else "⚠️"
                                print(f"         {status} {ticket_id}: session={ticket_data.get('session_id', 'N/A')}, user={ticket_data.get('user_id', 'N/A')}")
                except Exception as e:
                    print(f"      ⚠️  Erreur lecture JSON: {e}")
                
                return False
        else:
            print(f"      ❌ Erreur récupération tickets: {tickets_response.status_code}")
            return False
    except Exception as e:
        print(f"      ❌ Erreur: {e}")
        return False

def test_data_persistence():
    """Test 6: Persistance des données"""
    print_section("TEST 6: Persistance des données")
    
    files_to_check = [
        "data/tickets.json",
        "data/sessions.json",
        "data/conversation_history.json",
        "data/orders.json"
    ]
    
    all_ok = True
    for file_path in files_to_check:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    count = len(data)
                elif isinstance(data, list):
                    count = len(data)
                else:
                    count = 0
                print(f"   ✅ {file_path}: {count} entrées")
        except FileNotFoundError:
            print(f"   ⚠️  {file_path}: Fichier non trouvé")
        except Exception as e:
            print(f"   ❌ {file_path}: Erreur - {e}")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale"""
    print("=" * 70)
    print("  TEST COMPLET DU BACKEND")
    print("=" * 70)
    
    results = []
    
    # Test 1: API Health
    results.append(("Santé de l'API", test_api_health()))
    
    if not results[0][1]:
        print("\n❌ L'API n'est pas disponible. Arrêt des tests.")
        return
    
    # Test 2: Endpoints
    results.append(("Endpoints API", test_all_endpoints()))
    
    # Test 3: Session
    session_id, user_id = test_session_creation()
    if session_id:
        results.append(("Création de session", True))
    else:
        results.append(("Création de session", False))
        print("\n❌ Impossible de créer une session. Arrêt des tests.")
        return
    
    # Test 4: Agents
    results.append(("Tous les agents", test_all_agents(session_id, user_id)))
    
    # Test 5: Tickets
    results.append(("Création de tickets", test_ticket_creation(session_id, user_id)))
    
    # Test 6: Persistance
    results.append(("Persistance des données", test_data_persistence()))
    
    # Résumé
    print("\n" + "=" * 70)
    print("  RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSÉ" if passed else "❌ ÉCHOUÉ"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ TOUS LES TESTS SONT PASSÉS - LE BACKEND FONCTIONNE PARFAITEMENT!")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFIE LES DÉTAILS CI-DESSUS")
    print("=" * 70)

if __name__ == "__main__":
    main()

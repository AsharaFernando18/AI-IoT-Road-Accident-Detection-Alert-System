"""Test Telegram notification sending directly"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.telegram_notifications import notify_nearest_responders

# Test accident at KLCC
test_accident = {
    'latitude': 3.1578,
    'longitude': 101.7123,
    'severity': 'high',
    'location': 'KLCC Area - Test Accident',
    'city': 'Kuala Lumpur',
    'timestamp': '2025-11-25T00:35:00',
    'description': 'Test notification - checking Telegram delivery'
}

print("\n" + "="*80)
print("🧪 TESTING TELEGRAM NOTIFICATION SYSTEM")
print("="*80)
print(f"\n📍 Test Accident Location: {test_accident['location']}")
print(f"📍 Coordinates: {test_accident['latitude']}, {test_accident['longitude']}")
print(f"🔴 Severity: {test_accident['severity']}\n")

try:
    print("🚀 Sending notifications to nearest responders...\n")
    results = notify_nearest_responders(test_accident, limit_per_type=3)
    
    print("="*80)
    print("📊 NOTIFICATION RESULTS")
    print("="*80)
    
    total_sent = 0
    total_failed = 0
    
    for resp_type, responder_results in results.items():
        print(f"\n🚑 {resp_type.upper()}:")
        if not responder_results:
            print(f"   ⚠️  No {resp_type} responders found nearby")
            continue
            
        for result in responder_results:
            if result['notified']:
                total_sent += 1
                print(f"   ✅ {result['username']} - {result['distance_km']:.2f} km - MESSAGE SENT")
            else:
                total_failed += 1
                error = result.get('error', 'Unknown error')
                print(f"   ❌ {result['username']} - {result['distance_km']:.2f} km - FAILED: {error}")
    
    print("\n" + "="*80)
    print(f"📈 SUMMARY: {total_sent} sent, {total_failed} failed")
    print("="*80)
    
    if total_sent > 0:
        print("\n✅ SUCCESS! Check Telegram app for notifications.")
    else:
        print("\n❌ NO NOTIFICATIONS SENT! Check errors above.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

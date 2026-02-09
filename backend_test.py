#!/usr/bin/env python3
"""
Life OS Backend API Testing Suite
Testing all critical endpoints with comprehensive coverage
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import time
import os


class LifeOSAPITester:
    def __init__(self, base_url="https://life-os-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_result(self, test_name, success, response=None, error=None):
        """Log test results with details"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        
        if success:
            self.tests_passed += 1
            if response:
                print(f"   Response: {response.status_code}")
        else:
            self.failed_tests.append({
                "test": test_name,
                "error": str(error) if error else "Unknown error",
                "status_code": response.status_code if response else None,
                "response": response.text[:200] if response else None
            })
            if error:
                print(f"   Error: {error}")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")

    def test_health_check(self):
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            self.log_result("Health Check", success, response)
            return success
        except Exception as e:
            self.log_result("Health Check", False, error=str(e))
            return False

    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # Generate unique user for testing
            timestamp = int(time.time())
            test_user = {
                "name": f"Test User {timestamp}",
                "email": f"test{timestamp}@lifeos.com",
                "password": "TestPass123!"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "token" in data and "user" in data:
                    self.token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    print(f"   Registered user: {test_user['email']}")
                else:
                    success = False
            
            self.log_result("User Registration", success, response)
            return success
        except Exception as e:
            self.log_result("User Registration", False, error=str(e))
            return False

    def test_existing_user_login(self):
        """Test login with existing test user"""
        try:
            login_data = {
                "email": "teste@lifeos.com",
                "password": "123456"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "token" in data and "user" in data:
                    self.token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    print(f"   Logged in as: {login_data['email']}")
                else:
                    success = False
            
            self.log_result("Existing User Login", success, response)
            return success
        except Exception as e:
            self.log_result("Existing User Login", False, error=str(e))
            return False

    def test_get_user_profile(self):
        """Test GET /api/auth/me endpoint"""
        if not self.token:
            self.log_result("Get User Profile", False, error="No auth token available")
            return False
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/me",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "id" in data and "email" in data:
                    print(f"   User: {data.get('name', 'Unknown')} ({data.get('email', 'No email')})")
                else:
                    success = False
            
            self.log_result("Get User Profile", success, response)
            return success
        except Exception as e:
            self.log_result("Get User Profile", False, error=str(e))
            return False

    def test_user_onboarding(self):
        """Test POST /api/user/onboarding endpoint"""
        if not self.token:
            self.log_result("User Onboarding", False, error="No auth token available")
            return False
            
        try:
            onboarding_data = {
                "age": 30,
                "weight": 75.0,
                "height": 175.0,
                "gender": "male",
                "activity_level": "moderate",
                "goal": "maintain",
                "restrictions": ["lactose"]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/user/onboarding",
                json=onboarding_data,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "calorie_target" in data:
                    print(f"   Calorie target set: {data['calorie_target']} kcal")
                else:
                    success = False
            
            self.log_result("User Onboarding", success, response)
            return success
        except Exception as e:
            self.log_result("User Onboarding", False, error=str(e))
            return False

    def test_get_user_quota(self):
        """Test GET /api/user/quota endpoint"""
        if not self.token:
            self.log_result("Get User Quota", False, error="No auth token available")
            return False
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/user/quota",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "quotas" in data and "plan" in data:
                    print(f"   Plan: {data['plan']}")
                    print(f"   Quotas available: {len(data['quotas'])} features")
                else:
                    success = False
            
            self.log_result("Get User Quota", success, response)
            return success
        except Exception as e:
            self.log_result("Get User Quota", False, error=str(e))
            return False

    def test_food_search(self):
        """Test GET /api/nutrition/foods/search endpoint"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/nutrition/foods/search?q=arroz",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "foods" in data:
                    print(f"   Found {len(data['foods'])} food items for 'arroz'")
                else:
                    success = False
            
            self.log_result("Food Search", success, response)
            return success
        except Exception as e:
            self.log_result("Food Search", False, error=str(e))
            return False

    def test_nutrition_text_analysis(self):
        """Test POST /api/nutrition/analyze-text endpoint"""
        if not self.token:
            self.log_result("Nutrition Text Analysis", False, error="No auth token available")
            return False
            
        try:
            analysis_data = {
                "text": "Comi arroz e feijão no almoço",
                "meal_type": "almoço"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/nutrition/analyze-text",
                json=analysis_data,
                timeout=20  # AI analysis takes time
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "meal_id" in data and "items" in data:
                    print(f"   Meal ID: {data['meal_id']}")
                    print(f"   Items analyzed: {len(data['items'])}")
                    if "total" in data:
                        print(f"   Total calories: {data['total'].get('calories', 0)}")
                else:
                    success = False
            
            self.log_result("Nutrition Text Analysis", success, response)
            return success
        except Exception as e:
            self.log_result("Nutrition Text Analysis", False, error=str(e))
            return False

    def test_create_event(self):
        """Test POST /api/agenda/events endpoint"""
        if not self.token:
            self.log_result("Create Event", False, error="No auth token available")
            return False
            
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            event_data = {
                "title": "Meeting with Team",
                "date": tomorrow,
                "time": "14:00",
                "end_time": "15:00",
                "location": "Conference Room",
                "notes": "Test event created via API",
                "reminder_email": True,
                "reminder_whatsapp": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/agenda/events",
                json=event_data,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "id" in data and "title" in data:
                    self.test_event_id = data["id"]  # Save for cleanup
                    print(f"   Event created: {data['title']} on {data['date']}")
                else:
                    success = False
            
            self.log_result("Create Event", success, response)
            return success
        except Exception as e:
            self.log_result("Create Event", False, error=str(e))
            return False

    def test_get_events(self):
        """Test GET /api/agenda/events endpoint"""
        if not self.token:
            self.log_result("Get Events", False, error="No auth token available")
            return False
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/agenda/events?period=week",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "events" in data:
                    print(f"   Found {len(data['events'])} events this week")
                else:
                    success = False
            
            self.log_result("Get Events", success, response)
            return success
        except Exception as e:
            self.log_result("Get Events", False, error=str(e))
            return False

    def test_delete_event(self):
        """Test DELETE /api/agenda/events/{id} endpoint"""
        if not self.token:
            self.log_result("Delete Event", False, error="No auth token available")
            return False
            
        if not hasattr(self, 'test_event_id'):
            self.log_result("Delete Event", False, error="No test event created")
            return False
            
        try:
            response = self.session.delete(
                f"{self.base_url}/api/agenda/events/{self.test_event_id}",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "message" in data:
                    print(f"   {data['message']}")
            
            self.log_result("Delete Event", success, response)
            return success
        except Exception as e:
            self.log_result("Delete Event", False, error=str(e))
            return False

    def test_create_bill(self):
        """Test POST /api/finance/bills endpoint"""
        if not self.token:
            self.log_result("Create Bill", False, error="No auth token available")
            return False
            
        try:
            next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            bill_data = {
                "name": "Internet Bill",
                "amount": 99.90,
                "due_date": next_month,
                "category": "Utilities",
                "recurrence": "monthly",
                "notes": "Test bill created via API"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/finance/bills",
                json=bill_data,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "id" in data and "name" in data:
                    self.test_bill_id = data["id"]  # Save for cleanup
                    print(f"   Bill created: {data['name']} - R$ {data['amount']}")
                else:
                    success = False
            
            self.log_result("Create Bill", success, response)
            return success
        except Exception as e:
            self.log_result("Create Bill", False, error=str(e))
            return False

    def test_create_expense(self):
        """Test POST /api/finance/expenses endpoint"""
        if not self.token:
            self.log_result("Create Expense", False, error="No auth token available")
            return False
            
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            expense_data = {
                "amount": 25.50,
                "date": today,
                "category": "Food",
                "description": "Test lunch expense"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/finance/expenses",
                json=expense_data,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "id" in data and "amount" in data:
                    print(f"   Expense created: R$ {data['amount']} - {data['description']}")
                else:
                    success = False
            
            self.log_result("Create Expense", success, response)
            return success
        except Exception as e:
            self.log_result("Create Expense", False, error=str(e))
            return False

    def test_get_finance_dashboard(self):
        """Test GET /api/finance/dashboard endpoint"""
        if not self.token:
            self.log_result("Get Finance Dashboard", False, error="No auth token available")
            return False
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/finance/dashboard",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "total_expenses" in data and "current_month" in data:
                    print(f"   Current month expenses: R$ {data['total_expenses']}")
                    print(f"   Pending bills: R$ {data.get('total_pending_bills', 0)}")
                else:
                    success = False
            
            self.log_result("Get Finance Dashboard", success, response)
            return success
        except Exception as e:
            self.log_result("Get Finance Dashboard", False, error=str(e))
            return False

    def test_ai_chat_nutrition(self):
        """Test POST /api/chat/message endpoint with nutrition module"""
        if not self.token:
            self.log_result("AI Chat Nutrition", False, error="No auth token available")
            return False
            
        try:
            chat_data = {
                "message": "arroz e feijão",
                "module": "nutrition"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat/message",
                json=chat_data,
                timeout=25  # AI processing takes time
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                if "message" in data and "module" in data:
                    print(f"   AI Response length: {len(data['message'])} chars")
                    print(f"   Module: {data['module']}")
                    if "data" in data and data["data"].get("meal_id"):
                        print(f"   Meal registered: {data['data']['meal_id']}")
                else:
                    success = False
            
            self.log_result("AI Chat Nutrition", success, response)
            return success
        except Exception as e:
            self.log_result("AI Chat Nutrition", False, error=str(e))
            return False

    def run_all_tests(self):
        """Execute all API tests in sequence"""
        print("=" * 60)
        print("🧪 LIFE OS BACKEND API TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()

        # Core API tests
        print("🔧 CORE API TESTS")
        print("-" * 30)
        self.test_health_check()
        print()

        # Authentication tests
        print("🔐 AUTHENTICATION TESTS")
        print("-" * 30)
        # Try with existing user first
        login_success = self.test_existing_user_login()
        if not login_success:
            # Fallback to registration
            self.test_user_registration()
        
        self.test_get_user_profile()
        self.test_user_onboarding()
        self.test_get_user_quota()
        print()

        # Nutrition tests
        print("🥗 NUTRITION MODULE TESTS")
        print("-" * 30)
        self.test_food_search()
        self.test_nutrition_text_analysis()
        print()

        # Agenda tests
        print("📅 AGENDA MODULE TESTS")
        print("-" * 30)
        self.test_create_event()
        self.test_get_events()
        self.test_delete_event()
        print()

        # Finance tests
        print("💰 FINANCE MODULE TESTS")
        print("-" * 30)
        self.test_create_bill()
        self.test_create_expense()
        self.test_get_finance_dashboard()
        print()

        # AI Chat tests
        print("🤖 AI CHAT TESTS")
        print("-" * 30)
        self.test_ai_chat_nutrition()
        print()

        # Results summary
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        print()

        if self.failed_tests:
            print("❌ FAILED TESTS DETAILS:")
            print("-" * 30)
            for fail in self.failed_tests:
                print(f"• {fail['test']}")
                print(f"  Error: {fail['error']}")
                if fail['status_code']:
                    print(f"  Status: {fail['status_code']}")
                print()

        print("=" * 60)
        return len(self.failed_tests) == 0


def main():
    """Run the complete test suite"""
    tester = LifeOSAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Test script for CarbonIQ Reward System

This script demonstrates how to test the reward system functionality.
Run this after setting up the API to verify everything works correctly.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class RewardSystemTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def register_and_login(self):
        """Register test user and get auth token"""
        try:
            # Register user
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Test User",
                "role": "student"
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/auth/register",
                json=register_data
            ) as resp:
                if resp.status == 200:
                    print("✅ User registered successfully")
                elif resp.status == 400:
                    print("ℹ️ User already exists, proceeding to login")
                else:
                    print(f"❌ Registration failed: {await resp.text()}")
                    return False
            
            # Login to get token
            login_data = {
                "username": TEST_USER_EMAIL,  # FastAPI OAuth2 expects 'username'
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/auth/login",
                data=login_data  # Form data for OAuth2
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.auth_token = result["access_token"]
                    print("✅ Login successful")
                    return True
                else:
                    print(f"❌ Login failed: {await resp.text()}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def test_initial_profile(self):
        """Test getting initial user profile"""
        print("\n🔍 Testing initial user profile...")
        
        try:
            async with self.session.get(
                f"{API_BASE_URL}/rewards/profile",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    profile = await resp.json()
                    print(f"✅ Initial profile loaded")
                    print(f"   Points: {profile['stats']['total_points']}")
                    print(f"   Reports: {profile['stats']['total_reports']}")
                    print(f"   Badges: {len(profile['stats']['badges_earned'])}")
                    print(f"   Level: {profile['level']}")
                    return profile
                else:
                    print(f"❌ Failed to get profile: {await resp.text()}")
                    return None
        except Exception as e:
            print(f"❌ Profile error: {e}")
            return None
    
    async def create_test_report(self, report_num=1):
        """Create a test waste report"""
        print(f"\n📝 Creating test report #{report_num}...")
        
        report_data = {
            "student_id": f"TEST{report_num:03d}",
            "waste_type": ["organic", "recyclable_plastic", "mixed"][report_num % 3],
            "location": {
                "type": "Point", 
                "coordinates": [-1.286389 + (report_num * 0.001), 36.817223 + (report_num * 0.001)]
            },
            "safe": True,
            "urban_area": True,
            "children_present": report_num % 4 == 0,
            "measure_height_cm": 50.0 + (report_num * 5),
            "measure_width_cm": 30.0 + (report_num * 3),
            "feedback": f"Test report #{report_num} with detailed feedback"
        }
        
        try:
            async with self.session.post(
                f"{API_BASE_URL}/reports/",
                json=report_data,
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    report = await resp.json()
                    print(f"✅ Report created successfully (ID: {report['id']})")
                    return report
                else:
                    print(f"❌ Failed to create report: {await resp.text()}")
                    return None
        except Exception as e:
            print(f"❌ Report creation error: {e}")
            return None
    
    async def check_rewards_after_reports(self):
        """Check rewards and achievements after creating reports"""
        print("\n🏆 Checking rewards and achievements...")
        
        try:
            # Get updated profile
            async with self.session.get(
                f"{API_BASE_URL}/rewards/profile",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    profile = await resp.json()
                    print(f"✅ Updated profile:")
                    print(f"   Points: {profile['stats']['total_points']}")
                    print(f"   Reports: {profile['stats']['total_reports']}")
                    print(f"   Badges: {profile['stats']['badges_earned']}")
                    print(f"   Level: {profile['level']}")
                    print(f"   Current Streak: {profile['stats']['current_streak']}")
                    
                    # Show recent rewards
                    if profile['recent_rewards']:
                        print(f"   Recent Rewards:")
                        for reward in profile['recent_rewards'][:5]:
                            print(f"     - {reward['description']}: {reward.get('points', 0)} points")
                    
                    return profile
        except Exception as e:
            print(f"❌ Rewards check error: {e}")
            return None
    
    async def test_leaderboard(self):
        """Test leaderboard functionality"""
        print("\n📊 Testing leaderboard...")
        
        try:
            # Get user rank
            async with self.session.get(
                f"{API_BASE_URL}/rewards/my-rank",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    rank = await resp.json()
                    print(f"✅ Your rank: #{rank['rank']}")
                    print(f"   Points: {rank['total_points']}")
                    print(f"   Reports: {rank['total_reports']}")
            
            # Get global leaderboard (top 10)
            async with self.session.get(
                f"{API_BASE_URL}/rewards/leaderboard/global?limit=10",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    leaderboard = await resp.json()
                    print(f"✅ Global Leaderboard (Top 10):")
                    for entry in leaderboard[:5]:  # Show top 5
                        print(f"   #{entry['rank']}: {entry['full_name']} - {entry['total_points']} pts")
                        
        except Exception as e:
            print(f"❌ Leaderboard error: {e}")
    
    async def test_achievements(self):
        """Test achievement progress"""
        print("\n🎯 Testing achievement progress...")
        
        try:
            async with self.session.get(
                f"{API_BASE_URL}/rewards/achievements",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    achievements = await resp.json()
                    print(f"✅ Achievement Progress:")
                    
                    # Show progress on first 5 achievements
                    for achievement in achievements[:5]:
                        progress_percent = achievement['progress_percentage']
                        status = "🏆" if achievement['completed'] else "🎯"
                        print(f"   {status} {achievement['name']}: {achievement['progress']}/{achievement['target']} ({progress_percent:.1f}%)")
                        print(f"      {achievement['description']}")
                        
        except Exception as e:
            print(f"❌ Achievements error: {e}")
    
    async def test_badge_info(self):
        """Test badge information endpoint"""
        print("\n🏅 Testing badge information...")
        
        try:
            async with self.session.get(
                f"{API_BASE_URL}/rewards/badges",
                headers=self.get_headers()
            ) as resp:
                if resp.status == 200:
                    badge_info = await resp.json()
                    print(f"✅ Total badges available: {badge_info['total_badges']}")
                    
                    # Show first few badges
                    for badge_type, info in list(badge_info['badges'].items())[:3]:
                        print(f"   🏅 {info['name']}: {info['description']}")
                        
        except Exception as e:
            print(f"❌ Badge info error: {e}")
    
    async def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting CarbonIQ Reward System Test")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Authentication
            if not await self.register_and_login():
                return
            
            # Initial state
            await self.test_initial_profile()
            
            # Badge information
            await self.test_badge_info()
            
            # Create some reports to trigger rewards
            for i in range(1, 4):  # Create 3 reports
                await self.create_test_report(i)
                await asyncio.sleep(1)  # Small delay between reports
            
            # Check rewards after reports
            await self.check_rewards_after_reports()
            
            # Test achievements
            await self.test_achievements()
            
            # Test leaderboard
            await self.test_leaderboard()
            
            print("\n🎉 Test completed successfully!")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    tester = RewardSystemTester()
    await tester.run_full_test()

if __name__ == "__main__":
    print("CarbonIQ Reward System Tester")
    print("Make sure your API is running on http://localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

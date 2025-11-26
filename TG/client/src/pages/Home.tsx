import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { APP_LOGO, APP_TITLE, getLoginUrl } from "@/const";
import { Link } from "wouter";

/**
 * Home page with link to the Real User Redirection landing page.
 */
export default function Home() {
  // The userAuth hooks provides authentication state
  let { user, loading, error, isAuthenticated, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
        <h1 className="text-3xl font-bold">Real User Redirection System</h1>
        <p className="text-blue-100 mt-2">Ultra-Next-Level Traffic Mechanism</p>
      </header>

      <main className="flex-1 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to the System</h2>
            <p className="text-gray-600 mb-6">
              This is the Real User Redirection System - an advanced mechanism that attracts and redirects real human users to a desired destination.
            </p>

            <div className="space-y-4 mb-6">
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">Key Features</h3>
                <ul className="text-gray-700 space-y-2 text-sm">
                  <li>✓ High-conversion landing page</li>
                  <li>✓ Real user tracking and analytics</li>
                  <li>✓ JavaScript-based redirection</li>
                  <li>✓ Campaign management</li>
                  <li>✓ Real-time conversion monitoring</li>
                </ul>
              </div>
            </div>

            <Link href="/redirect">
              <Button className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 rounded-lg">
                View Landing Page
              </Button>
            </Link>
          </div>

          {isAuthenticated && (
            <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
              <p className="text-green-900">
                Welcome, {user?.name || 'User'}! You are authenticated.
              </p>
              <Button onClick={logout} variant="outline" className="mt-2">
                Logout
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

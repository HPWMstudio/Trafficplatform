import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { trpc } from "@/lib/trpc";
import { v4 as uuidv4 } from "uuid";

/**
 * High-Conversion Landing Page for Real User Redirection
 * 
 * This page is designed to:
 * 1. Attract real human users with compelling copy and design
 * 2. Log user metadata (IP, User-Agent, Referer, Device Type)
 * 3. Execute JavaScript-based redirection to the target URL
 * 4. Track conversion metrics for analytics
 */

export default function Redirect() {
  // Get query parameters from URL
  const searchParams = new URLSearchParams(window.location.search);
  const targetUrl = searchParams.get("targetUrl") || "https://example.com";
  const campaignId = searchParams.get("campaignId") || "default";

  const [visitorId] = useState(() => uuidv4());
  const [sessionStart] = useState(Date.now());
  const [redirected, setRedirected] = useState(false);
  const [deviceType, setDeviceType] = useState("desktop");

  // tRPC mutations for logging
  const logVisitMutation = trpc.redirect.logVisit.useMutation();
  const markRedirectedMutation = trpc.redirect.markRedirected.useMutation();

  /**
   * Detect device type based on User-Agent
   */
  const detectDeviceType = () => {
    const ua = navigator.userAgent.toLowerCase();
    if (/mobile|android|iphone|ipad|phone/i.test(ua)) return "mobile";
    if (/tablet|ipad/i.test(ua)) return "tablet";
    return "desktop";
  };

  /**
   * Get visitor's IP address (client-side approximation)
   */
  const getClientIP = async () => {
    try {
      const response = await fetch("https://api.ipify.org?format=json");
      const data = await response.json();
      return data.ip || "unknown";
    } catch {
      return "unknown";
    }
  };

  /**
   * Log the user visit to the database
   */
  const logUserVisit = async () => {
    const device = detectDeviceType();
    setDeviceType(device);

    const ipAddress = await getClientIP();

    const visitData = {
      visitorId,
      targetUrl,
      userAgent: navigator.userAgent,
      referer: document.referrer || "direct",
      ipAddress,
      deviceType: device,
      country: "unknown",
    };

    // Log to database
    logVisitMutation.mutate(visitData);
  };

  /**
   * Execute the redirection
   */
  const executeRedirect = async () => {
    if (redirected) return;

    const redirectTime = Date.now() - sessionStart;
    const sessionDuration = redirectTime;

    // Mark as redirected in database
    markRedirectedMutation.mutate({
      visitorId,
      redirectTime,
      sessionDuration,
    });

    setRedirected(true);

    // Delay redirect slightly to ensure database logging
    setTimeout(() => {
      window.location.href = targetUrl;
    }, 500);
  };

  /**
   * Initialize on component mount
   */
  useEffect(() => {
    logUserVisit();
  }, []);

  /**
   * Auto-redirect after 5 seconds if user hasn't clicked
   */
  useEffect(() => {
    const autoRedirectTimer = setTimeout(() => {
      if (!redirected) {
        executeRedirect();
      }
    }, 5000);

    return () => clearTimeout(autoRedirectTimer);
  }, [redirected]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Exclusive Offer
          </h1>
          <p className="text-gray-600 text-sm">
            You have been selected for a special opportunity
          </p>
        </div>

        {/* Main Content */}
        <div className="space-y-4 mb-6">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
            <p className="text-gray-800 font-semibold mb-2">
              Limited Time Offer
            </p>
            <p className="text-gray-600 text-sm">
              Click below to claim your exclusive reward before it expires.
            </p>
          </div>

          {/* Features/Benefits */}
          <div className="space-y-2">
            <div className="flex items-start gap-3">
              <span className="text-green-500 font-bold">✓</span>
              <span className="text-gray-700 text-sm">Instant activation</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500 font-bold">✓</span>
              <span className="text-gray-700 text-sm">No hidden fees</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500 font-bold">✓</span>
              <span className="text-gray-700 text-sm">100% satisfaction guaranteed</span>
            </div>
          </div>
        </div>

        {/* CTA Button */}
        <Button
          onClick={executeRedirect}
          disabled={redirected}
          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 rounded-lg mb-3 transition-all"
        >
          {redirected ? "Redirecting..." : "Claim Your Offer Now"}
        </Button>

        {/* Secondary Text */}
        <p className="text-center text-gray-500 text-xs">
          Redirecting in {redirected ? "..." : "5"} seconds
        </p>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-center text-gray-500 text-xs">
            By clicking, you agree to our terms and privacy policy
          </p>
        </div>
      </div>

      {/* Debug Info */}
      <div className="fixed bottom-4 right-4 text-xs text-gray-500 bg-gray-100 p-2 rounded max-w-xs">
        <p>Visitor ID: {visitorId.substring(0, 8)}...</p>
        <p>Device: {deviceType}</p>
        <p>Campaign: {campaignId}</p>
      </div>
    </div>
  );
}

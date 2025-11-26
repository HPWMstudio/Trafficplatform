import { useEffect, useState } from "react";
import { trpc } from "@/lib/trpc";
import { v4 as uuidv4 } from "uuid";

/**
 * The Interceptor: Cloaked Redirection Page
 * 
 * Logic:
 * 1. Detect User-Agent.
 * 2. If Bot (Twitter, Facebook, etc.) -> Show "Safe" Preview (Cloak).
 * 3. If Human -> Instant Redirect (Zero-UI).
 */

export default function Redirect() {
  const searchParams = new URLSearchParams(window.location.search);
  const targetUrl = searchParams.get("targetUrl") || "https://google.com";

  const [visitorId] = useState(() => uuidv4());
  const [isBot, setIsBot] = useState(false);

  // tRPC mutation
  const logVisitMutation = trpc.redirect.logVisit.useMutation();

  useEffect(() => {
    const checkUserAgent = () => {
      const ua = navigator.userAgent.toLowerCase();
      // Common social bots
      const botPatterns = [
        "twitterbot",
        "facebookexternalhit",
        "linkedinbot",
        "slackbot",
        "discordbot",
        "whatsapp",
        "telegrambot",
        "googlebot" // Optional: cloak from Google too?
      ];

      const detectedBot = botPatterns.some(bot => ua.includes(bot));
      setIsBot(detectedBot);

      return detectedBot;
    };

    const performRedirect = async () => {
      const bot = checkUserAgent();

      // Log visit regardless
      logVisitMutation.mutate({
        visitorId,
        targetUrl,
        userAgent: navigator.userAgent,
        referer: document.referrer || "direct",
        ipAddress: "unknown", // Client-side can't reliably get IP without API
        deviceType: bot ? "bot" : "human",
        country: "unknown",
      });

      if (!bot) {
        // HUMAN: Zero-Latency Redirect
        // Use replace to prevent back-button looping
        window.location.replace(targetUrl);
      }
    };

    performRedirect();
  }, []);

  if (isBot) {
    // CLOAKED CONTENT (What the bot/preview sees)
    // This mimics a generic "News" or "Video" site to generate a high-CTR preview card
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
        {/* Open Graph Metadata would ideally be server-side, but we simulate the visual here */}
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-md overflow-hidden">
          <div className="h-64 bg-gray-800 flex items-center justify-center">
            {/* Fake Video Player UI */}
            <div className="w-16 h-16 border-4 border-white rounded-full flex items-center justify-center">
              <div className="w-0 h-0 border-t-8 border-t-transparent border-l-12 border-l-white border-b-8 border-b-transparent ml-1"></div>
            </div>
          </div>
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Must Watch: Amazing Viral Video
            </h1>
            <p className="text-gray-600">
              You won't believe what happens next. Watch the full video now.
            </p>
            <div className="mt-4 flex items-center text-sm text-gray-500">
              <span>1.2M Views</span>
              <span className="mx-2">•</span>
              <span>2 hours ago</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // HUMAN CONTENT (Zero-UI)
  // Empty div while redirecting
  return <div className="bg-white min-h-screen"></div>;
}

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, Play, Square, Terminal, Globe, Users, Search } from "lucide-react";

// API URL from Environment (Production) or Localhost (Dev)
const C2_API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export default function AdminDashboard() {
    const [systemStatus, setSystemStatus] = useState<Record<string, string>>({});
    const [logs, setLogs] = useState<string[]>([]);
    const [commandType, setCommandType] = useState("SOCIAL");

    // Social Form State
    const [socialUrl, setSocialUrl] = useState("");
    const [socialContent, setSocialContent] = useState("");

    // SEO Form State
    const [seoKeyword, setSeoKeyword] = useState("");
    const [seoDomain, setSeoDomain] = useState("");

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${C2_API}/system/status`);
            if (res.ok) {
                const data = await res.json();
                setSystemStatus(data);
            }
        } catch (e) {
            console.error("Failed to fetch status", e);
        }
    };

    const toggleComponent = async (name: string, script: string, action: "start" | "stop") => {
        try {
            const endpoint = action === "start" ? "/system/start" : "/system/stop";
            await fetch(`${C2_API}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, script }),
            });
            addLog(`[SYSTEM] ${action.toUpperCase()} ${name}`);
            fetchStatus();
        } catch (e) {
            addLog(`[ERROR] Failed to ${action} ${name}`);
        }
    };

    const sendCommand = async () => {
        let payload = {};
        if (commandType === "SOCIAL") {
            payload = {
                action: "SOCIAL",
                sub_action: "INTERACT",
                target_url: socialUrl,
                content: socialContent
            };
        } else {
            payload = {
                action: "SEO",
                engine: "google",
                keyword: seoKeyword,
                target_domain: seoDomain
            };
        }

        try {
            const res = await fetch(`${C2_API}/commands`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            addLog(`[CMD] Sent ${commandType} command: ID ${data.command_id}`);
        } catch (e) {
            addLog(`[ERROR] Failed to send command`);
        }
    };

    const addLog = (msg: string) => {
        setLogs(prev => [`${new Date().toLocaleTimeString()} ${msg}`, ...prev.slice(0, 19)]);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            Ultimate Traffic Platform
                        </h1>
                        <p className="text-gray-400">Control Center</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${Object.keys(systemStatus).length > 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm font-mono">C2 SERVER: {Object.keys(systemStatus).length > 0 ? 'ONLINE' : 'OFFLINE'}</span>
                    </div>
                </div>

                {/* System Status Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Monitor Agent */}
                    <StatusCard
                        title="Monitor Agent"
                        icon={<Activity className="w-6 h-6 text-blue-400" />}
                        status={systemStatus["Monitor Agent"] || "Stopped"}
                        onStart={() => toggleComponent("Monitor Agent", "monitor_agent.py", "start")}
                        onStop={() => toggleComponent("Monitor Agent", "monitor_agent.py", "stop")}
                    />

                    {/* Bot Client */}
                    <StatusCard
                        title="Bot Client"
                        icon={<Users className="w-6 h-6 text-purple-400" />}
                        status={systemStatus["Bot Client"] || "Stopped"}
                        onStart={() => toggleComponent("Bot Client", "bot_client_v3.py", "start")}
                        onStop={() => toggleComponent("Bot Client", "bot_client_v3.py", "stop")}
                    />

                    {/* SEO Agent */}
                    <StatusCard
                        title="SEO Agent"
                        icon={<Search className="w-6 h-6 text-green-400" />}
                        status={systemStatus["SEO Agent"] || "Stopped"}
                        onStart={() => toggleComponent("SEO Agent", "bot_client_v3.py", "start")} // Reuses bot client
                        onStop={() => toggleComponent("SEO Agent", "bot_client_v3.py", "stop")}
                    />
                </div>

                {/* Main Control Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Command Builder */}
                    <Card className="lg:col-span-2 bg-gray-800 border-gray-700">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Terminal className="w-5 h-5" />
                                Task Builder
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Tabs defaultValue="SOCIAL" onValueChange={setCommandType} className="w-full">
                                <TabsList className="grid w-full grid-cols-2 bg-gray-900">
                                    <TabsTrigger value="SOCIAL">Social Interception</TabsTrigger>
                                    <TabsTrigger value="SEO">SEO Boost</TabsTrigger>
                                </TabsList>

                                <TabsContent value="SOCIAL" className="space-y-4 mt-4">
                                    <div className="space-y-2">
                                        <label className="text-sm text-gray-400">Target Post URL</label>
                                        <Input
                                            placeholder="https://twitter.com/..."
                                            className="bg-gray-900 border-gray-600"
                                            value={socialUrl}
                                            onChange={e => setSocialUrl(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm text-gray-400">Reply Content (Spintax supported)</label>
                                        <Input
                                            placeholder="Check this out: {link}"
                                            className="bg-gray-900 border-gray-600"
                                            value={socialContent}
                                            onChange={e => setSocialContent(e.target.value)}
                                        />
                                    </div>
                                </TabsContent>

                                <TabsContent value="SEO" className="space-y-4 mt-4">
                                    <div className="space-y-2">
                                        <label className="text-sm text-gray-400">Search Keyword</label>
                                        <Input
                                            placeholder="best traffic generator"
                                            className="bg-gray-900 border-gray-600"
                                            value={seoKeyword}
                                            onChange={e => setSeoKeyword(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm text-gray-400">Target Domain to Click</label>
                                        <Input
                                            placeholder="my-redirect-site.com"
                                            className="bg-gray-900 border-gray-600"
                                            value={seoDomain}
                                            onChange={e => setSeoDomain(e.target.value)}
                                        />
                                    </div>
                                </TabsContent>

                                <Button onClick={sendCommand} className="w-full mt-6 bg-blue-600 hover:bg-blue-700">
                                    <Play className="w-4 h-4 mr-2" />
                                    Dispatch Task
                                </Button>
                            </Tabs>
                        </CardContent>
                    </Card>

                    {/* Live Logs */}
                    <Card className="bg-gray-800 border-gray-700">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Globe className="w-5 h-5" />
                                Live Activity
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[300px] bg-gray-950 rounded-md p-4 font-mono text-xs overflow-y-auto space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="text-green-400 border-b border-gray-900 pb-1">
                                        {log}
                                    </div>
                                ))}
                                {logs.length === 0 && <span className="text-gray-600">Waiting for activity...</span>}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

function StatusCard({ title, icon, status, onStart, onStop }: any) {
    const isRunning = status === "Running";
    return (
        <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gray-900 rounded-lg">
                        {icon}
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg">{title}</h3>
                        <Badge variant={isRunning ? "default" : "destructive"} className={isRunning ? "bg-green-600" : "bg-red-900"}>
                            {status.toUpperCase()}
                        </Badge>
                    </div>
                </div>
                <div className="flex gap-2">
                    {!isRunning ? (
                        <Button size="icon" variant="outline" className="border-green-600 text-green-500 hover:bg-green-900" onClick={onStart}>
                            <Play className="w-4 h-4" />
                        </Button>
                    ) : (
                        <Button size="icon" variant="outline" className="border-red-600 text-red-500 hover:bg-red-900" onClick={onStop}>
                            <Square className="w-4 h-4" />
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

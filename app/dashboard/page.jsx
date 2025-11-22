import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, ClipboardList, Bell, LogOut } from "lucide-react";


export default function DashboardPage() {
return (
<div className="min-h-screen bg-gray-100 flex flex-col">
{/* Top Bar */}
<div className="w-full bg-white shadow p-4 flex justify-between items-center border-b">
<h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
<div className="flex items-center gap-6">
<Bell className="w-6 h-6 text-gray-700 cursor-pointer hover:text-teal-700" />
<User className="w-6 h-6 text-gray-700 cursor-pointer hover:text-teal-700" />
<LogOut className="w-6 h-6 text-gray-700 cursor-pointer hover:text-red-600" />
</div>
</div>
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">


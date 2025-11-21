"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  const { user } = useAuth();

  if (!user) return <div>Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-semibold mb-4">
        Welcome, {user.email}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Today's Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Tasks assigned for today will appear here.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deadlines</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Due dates & tax deadlines will appear here.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Client Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Password changes, requests, or messages appear here.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
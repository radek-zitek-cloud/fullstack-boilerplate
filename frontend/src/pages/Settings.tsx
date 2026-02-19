import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useTheme } from "@/contexts/ThemeContext";
import { Sun, Moon, Monitor, Palette } from "lucide-react";

export default function Settings() {
  const { mode, color, setMode, setColor, isDark } = useTheme();

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </CardTitle>
          <CardDescription>
            Customize the look and feel of the application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Theme Mode */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Theme Mode</Label>
            <RadioGroup
              value={mode}
              onValueChange={(value) => setMode(value as "light" | "dark" | "system")}
              className="grid grid-cols-3 gap-4"
            >
              <div>
                <RadioGroupItem value="light" id="light" className="peer sr-only" />
                <label
                  htmlFor="light"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                >
                  <Sun className="mb-3 h-6 w-6" />
                  <span className="text-sm font-medium">Light</span>
                </label>
              </div>

              <div>
                <RadioGroupItem value="dark" id="dark" className="peer sr-only" />
                <label
                  htmlFor="dark"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                >
                  <Moon className="mb-3 h-6 w-6" />
                  <span className="text-sm font-medium">Dark</span>
                </label>
              </div>

              <div>
                <RadioGroupItem value="system" id="system" className="peer sr-only" />
                <label
                  htmlFor="system"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                >
                  <Monitor className="mb-3 h-6 w-6" />
                  <span className="text-sm font-medium">System</span>
                </label>
              </div>
            </RadioGroup>
            <p className="text-sm text-muted-foreground">
              {mode === "system"
                ? "Automatically matches your system preference"
                : `Currently using ${isDark ? "dark" : "light"} mode`}
            </p>
          </div>

          {/* Color Variant */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Accent Color</Label>
            <RadioGroup
              value={color}
              onValueChange={(value) => setColor(value as "slate" | "blue" | "emerald")}
              className="grid grid-cols-3 gap-4"
            >
              <div>
                <RadioGroupItem value="slate" id="slate" className="peer sr-only" />
                <label
                  htmlFor="slate"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-slate-500 [&:has([data-state=checked])]:border-slate-500 cursor-pointer"
                >
                  <div className="w-6 h-6 rounded-full bg-slate-500 mb-3" />
                  <span className="text-sm font-medium">Slate</span>
                </label>
              </div>

              <div>
                <RadioGroupItem value="blue" id="blue" className="peer sr-only" />
                <label
                  htmlFor="blue"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-blue-500 [&:has([data-state=checked])]:border-blue-500 cursor-pointer"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-500 mb-3" />
                  <span className="text-sm font-medium">Blue</span>
                </label>
              </div>

              <div>
                <RadioGroupItem value="emerald" id="emerald" className="peer sr-only" />
                <label
                  htmlFor="emerald"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-emerald-500 [&:has([data-state=checked])]:border-emerald-500 cursor-pointer"
                >
                  <div className="w-6 h-6 rounded-full bg-emerald-500 mb-3" />
                  <span className="text-sm font-medium">Emerald</span>
                </label>
              </div>
            </RadioGroup>
          </div>

          {/* Preview */}
          <div className="pt-4 border-t">
            <Label className="text-base font-medium mb-3 block">Preview</Label>
            <div className="p-4 rounded-lg border bg-card text-card-foreground">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-primary" />
                <div>
                  <p className="font-medium">Sample Card</p>
                  <p className="text-sm text-muted-foreground">This is how content looks</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="px-4 py-2 rounded bg-primary text-primary-foreground text-sm">
                  Primary
                </button>
                <button className="px-4 py-2 rounded bg-secondary text-secondary-foreground text-sm">
                  Secondary
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState, useEffect } from "react";
import { Settings, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const STORAGE_KEY = "m3-agent-names";

interface NameConfig {
  userRoleName: string;
  agentRoleName: string;
  apiRoleName: string;
}

const DEFAULT_NAMES: NameConfig = {
  userRoleName: "Kori",
  agentRoleName: "M3 AGENT",
  apiRoleName: "Kori-API",
};

export const useNameSettings = () => {
  const [names, setNames] = useState<NameConfig>(DEFAULT_NAMES);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setNames(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse stored names:", e);
      }
    }
  }, []);

  const updateNames = (newNames: NameConfig) => {
    setNames(newNames);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newNames));
  };

  return { names, updateNames };
};

export const NameSettingsDialog = () => {
  const { names, updateNames } = useNameSettings();
  const [open, setOpen] = useState(false);
  const [tempNames, setTempNames] = useState(names);

  useEffect(() => {
    setTempNames(names);
  }, [names, open]);

  const handleSave = () => {
    updateNames(tempNames);
    setOpen(false);
  };

  const handleReset = () => {
    setTempNames(DEFAULT_NAMES);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9"
          title="设置角色名称"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>角色名称设置</DialogTitle>
          <DialogDescription>
            自定义三角聊天室中各角色的显示名称
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="userRoleName">用户名称（User）</Label>
            <Input
              id="userRoleName"
              value={tempNames.userRoleName}
              onChange={(e) =>
                setTempNames({ ...tempNames, userRoleName: e.target.value })
              }
              placeholder="例如：Kori"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="agentRoleName">Agent名称</Label>
            <Input
              id="agentRoleName"
              value={tempNames.agentRoleName}
              onChange={(e) =>
                setTempNames({ ...tempNames, agentRoleName: e.target.value })
              }
              placeholder="例如：M3 AGENT"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="apiRoleName">API名称</Label>
            <Input
              id="apiRoleName"
              value={tempNames.apiRoleName}
              onChange={(e) =>
                setTempNames({ ...tempNames, apiRoleName: e.target.value })
              }
              placeholder="例如：Kori-API"
            />
          </div>
        </div>
        <div className="flex justify-between">
          <Button variant="outline" onClick={handleReset}>
            恢复默认
          </Button>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>保存</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

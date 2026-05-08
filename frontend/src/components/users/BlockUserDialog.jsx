import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ShieldOff } from "lucide-react";

export default function BlockUserDialog({ user, open, onClose, onBlock }) {
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  const handleBlock = async () => {
    setSaving(true);
    await onBlock(user.id, reason);
    setSaving(false);
    setReason("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <ShieldOff className="w-5 h-5" />
            Bloquear Usuário
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <p className="text-sm text-muted-foreground">
            Você está bloqueando{" "}
            <span className="font-semibold text-foreground">
              {user?.full_name || user?.email}
            </span>
            . O usuário não conseguirá acessar o sistema.
          </p>
          <div className="space-y-2">
            <Label>Motivo do bloqueio</Label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Ex: Inadimplência — fatura vencida em 01/05/2026"
              rows={3}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleBlock}
              disabled={saving || !reason.trim()}
            >
              <ShieldOff className="w-4 h-4 mr-2" />
              {saving ? "Bloqueando..." : "Bloquear Usuário"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

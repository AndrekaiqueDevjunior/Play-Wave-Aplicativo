import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  buscarMe,
  listarUsuarios,
  criarUsuario,
  atualizarUsuario,
  deletarUsuario,
  reenviarConviteUsuario,
} from "@/api/usuarios";
import { criarLog } from "@/api/userLogs";
import { useToast } from "@/components/ui/use-toast";
import { Link } from "react-router-dom";
import {
  Plus,
  Building2,
  Users,
  Send,
  MoreHorizontal,
  Pencil,
  ShieldOff,
  Shield,
  UserX,
  UserCheck,
  KeyRound,
  ClipboardList,
  Search,
  Trash2,
  MailWarning,
} from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import UserStatusBadge from "@/components/users/UserStatusBadge";
import EditUserDialog from "@/components/users/EditUserDialog";
import BlockUserDialog from "@/components/users/BlockUserDialog";
import UserLogDrawer from "@/components/users/UserLogDrawer";

const ROLE_LABELS = {
  admin: "Admin",
  operator: "Operador",
  viewer: "Visualizador",
};
const ROLE_COLORS = {
  admin: "bg-primary/10 text-primary border-primary/20",
  operator: "bg-amber-100 text-amber-700 border-amber-200",
  viewer: "bg-slate-100 text-slate-600 border-slate-200",
};

async function registrarLog(targetUserId, targetEmail, action, performedBy, details = "") {
  try {
    await criarLog({ target_user_id: targetUserId, target_user_email: targetEmail, action, performed_by: performedBy, details });
  } catch (err) {
    // O log de auditoria é opcional; não deve bloquear a ação principal.
    console.warn("Falha ao registrar log de usuário:", err?.message || err);
  }
}

export default function ConfigUsuarios() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  const [inviteOpen, setInviteOpen] = useState(false);
  const [invite, setInvite] = useState({
    name: "",
    email: "",
    role: "operator",
    accessMode: "invite", // "invite" (e-mail) | "password" (definida pelo admin)
    password: "",
  });
  const [inviteSaving, setInviteSaving] = useState(false);
  const [resendingId, setResendingId] = useState(null);

  const [editUser, setEditUser] = useState(null);
  const [blockUser, setBlockUser] = useState(null);
  const [logUser, setLogUser] = useState(null);

  // Usuário logado (para registrar responsável)
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => buscarMe(),
  });

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => listarUsuarios({ limit: 200 }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => atualizarUsuario(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deletarUsuario(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleInvite = async () => {
    setInviteSaving(true);
    try {
      const emailNormalizado = invite.email.trim().toLowerCase();
      const sendInvite = invite.accessMode === "invite";
      const payload = {
        name: invite.name.trim(),
        email: emailNormalizado,
        role: invite.role,
        send_invite: sendInvite,
      };
      if (!sendInvite) {
        payload.password = invite.password;
      }
      const created = await criarUsuario(payload);
      await registrarLog(
        created?.id || "pending",
        emailNormalizado,
        "invite",
        me?.email || "admin",
        sendInvite
          ? `Convite por e-mail para ${invite.name} (${invite.role})`
          : `Usuário criado com senha definida pelo admin para ${invite.name} (${invite.role})`,
      );
      toast({
        title: "Usuário criado!",
        description: sendInvite
          ? `Um e-mail de convite foi enviado para ${emailNormalizado}.`
          : `${emailNormalizado} já pode acessar com a senha definida.`,
      });
      setInviteOpen(false);
      setInvite({ name: "", email: "", role: "operator", accessMode: "invite", password: "" });
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (err) {
      toast({
        title: "Erro ao criar usuário",
        description: err?.message || "Não foi possível criar o usuário.",
        variant: "destructive",
      });
    } finally {
      setInviteSaving(false);
    }
  };

  const handleResendInvite = async (user) => {
    setResendingId(user.id);
    try {
      await reenviarConviteUsuario(user.id);
      await registrarLog(
        user.id,
        user.email,
        "resend_invite",
        me?.email || "admin",
        "Convite reenviado",
      );
      toast({ title: "Convite reenviado!", description: `Novo e-mail enviado para ${user.email}.` });
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (err) {
      toast({
        title: "Erro ao reenviar convite",
        description: err?.message || "Não foi possível reenviar o convite.",
        variant: "destructive",
      });
    } finally {
      setResendingId(null);
    }
  };

  const handleEdit = async (id, form) => {
    const user = users.find((u) => u.id === id);
    const payload = {};
    if (form.name !== undefined) payload.name = form.name.trim();
    if (form.email) payload.email = form.email.trim().toLowerCase();
    if (form.role) payload.role = form.role;
    if (form.job_title !== undefined) payload.job_title = form.job_title || null;
    await updateMutation.mutateAsync({ id, data: payload });
    await registrarLog(
      id,
      user?.email,
      "edit",
      me?.email || "admin",
      `Nome: ${form.name}, Cargo: ${form.job_title}, Permissão: ${form.role}`,
    );
    toast({ title: "Usuário atualizado!" });
  };

  const handleToggleActive = async (user) => {
    const isActive = (user.account_status || (user.is_active ? "active" : "inactive")) === "active";
    const action = isActive ? "deactivate" : "activate";
    await updateMutation.mutateAsync({
      id: user.id,
      data: {
        account_status: isActive ? "inactive" : "active",
        is_active: !isActive,
      },
    });
    await registrarLog(user.id, user.email, action, me?.email || "admin");
    toast({ title: isActive ? "Usuário desativado." : "Usuário ativado!" });
  };

  const handleBlock = async (id, reason) => {
    const user = users.find((u) => u.id === id);
    await updateMutation.mutateAsync({
      id,
      data: {
        account_status: "blocked",
        is_active: false,
        blocked_reason: reason,
      },
    });
    await registrarLog(id, user?.email, "block", me?.email || "admin", reason);
    toast({ title: "Usuário bloqueado.", variant: "destructive" });
  };

  const handleUnblock = async (user) => {
    await updateMutation.mutateAsync({
      id: user.id,
      data: {
        account_status: "active",
        is_active: true,
        blocked_reason: null,
      },
    });
    await registrarLog(user.id, user.email, "unblock", me?.email || "admin");
    toast({ title: "Usuário desbloqueado!" });
  };

  const handleResetPassword = async (user) => {
    // Sinaliza a ação — integração real enviaria email via FastAPI
    await registrarLog(
      user.id,
      user.email,
      "reset_password",
      me?.email || "admin",
      "Redefinição solicitada pelo admin",
    );
    toast({
      title: "Solicitação registrada!",
      description: `Um link de redefinição será enviado para ${user.email}`,
    });
  };

  const handleDelete = async (user) => {
    const label = user.name || user.full_name || user.email;
    if (!window.confirm(`Remover definitivamente o usuário ${label}?`)) return;
    try {
      await deleteMutation.mutateAsync(user.id);
      await registrarLog(user.id, user.email, "delete", me?.email || "admin", `Usuário removido: ${label}`);
      toast({ title: "Usuário removido." });
    } catch (err) {
      toast({
        title: "Erro ao remover usuário",
        description: err?.message || "Não foi possível remover o usuário.",
        variant: "destructive",
      });
    }
  };

  // ── Filtros ───────────────────────────────────────────────────────────────
  const filtered = users.filter((u) => {
    const matchSearch =
      !search ||
      (u.name || u.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (u.email || "").toLowerCase().includes(search.toLowerCase());
    const status = u.account_status || (u.is_active ? "active" : "inactive");
    const matchStatus =
      filterStatus === "all" || status === filterStatus;
    return matchSearch && matchStatus;
  });

  const counts = {
    total: users.length,
    active: users.filter((u) => (u.account_status || (u.is_active ? "active" : "inactive")) === "active")
      .length,
    inactive: users.filter((u) => (u.account_status || (u.is_active ? "active" : "inactive")) === "inactive").length,
    blocked: users.filter((u) => u.account_status === "blocked").length,
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Configurações</h2>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="company" asChild>
            <Link to="/configuracoes/empresa">
              <Building2 className="w-4 h-4 mr-2" />
              Empresa
            </Link>
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="w-4 h-4 mr-2" />
            Usuários
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-6 space-y-5">
          {/* Stats rápidos */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Total", value: counts.total, color: "text-foreground" },
              {
                label: "Ativos",
                value: counts.active,
                color: "text-emerald-600",
              },
              {
                label: "Inativos",
                value: counts.inactive,
                color: "text-slate-500",
              },
              {
                label: "Bloqueados",
                value: counts.blocked,
                color: "text-red-600",
              },
            ].map((s) => (
              <Card key={s.label}>
                <CardContent className="p-4">
                  <p className="text-xs text-muted-foreground">{s.label}</p>
                  <p className={`text-2xl font-bold mt-1 ${s.color}`}>
                    {s.value}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
            <div className="flex gap-2 flex-1 w-full sm:w-auto">
              <div className="relative flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Buscar usuário..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="active">Ativos</SelectItem>
                  <SelectItem value="inactive">Inativos</SelectItem>
                  <SelectItem value="blocked">Bloqueados</SelectItem>
                  <SelectItem value="pending_invite">Convite pendente</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Usuário
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Novo Usuário</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-2">
                  <div className="space-y-2">
                    <Label>Nome</Label>
                    <Input
                      value={invite.name}
                      onChange={(e) =>
                        setInvite({ ...invite, name: e.target.value })
                      }
                      placeholder="Nome completo"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>E-mail</Label>
                    <Input
                      type="email"
                      value={invite.email}
                      onChange={(e) =>
                        setInvite({ ...invite, email: e.target.value })
                      }
                      placeholder="email@empresa.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Permissão</Label>
                    <Select
                      value={invite.role}
                      onValueChange={(v) => setInvite({ ...invite, role: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="operator">Operador</SelectItem>
                        <SelectItem value="viewer">Visualizador</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Como conceder acesso</Label>
                    <Select
                      value={invite.accessMode}
                      onValueChange={(v) => setInvite({ ...invite, accessMode: v, password: "" })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="invite">Enviar convite por e-mail</SelectItem>
                        <SelectItem value="password">Definir senha agora</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {invite.accessMode === "invite"
                        ? "O usuário recebe um e-mail com um link para criar a própria senha."
                        : "Você define a senha inicial; o usuário poderá trocá-la depois."}
                    </p>
                  </div>
                  {invite.accessMode === "password" && (
                    <div className="space-y-2">
                      <Label>Senha</Label>
                      <Input
                        type="password"
                        value={invite.password}
                        onChange={(e) => setInvite({ ...invite, password: e.target.value })}
                        placeholder="Mínimo de 6 caracteres"
                      />
                    </div>
                  )}
                  <div className="flex justify-end gap-3">
                    <Button
                      variant="outline"
                      onClick={() => setInviteOpen(false)}
                    >
                      Cancelar
                    </Button>
                    <Button
                      onClick={handleInvite}
                      disabled={
                        inviteSaving ||
                        !invite.email ||
                        !invite.name ||
                        (invite.accessMode === "password" && invite.password.length < 6)
                      }
                    >
                      <Send className="w-4 h-4 mr-2" />
                      {inviteSaving ? "Criando..." : "Criar Usuário"}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Tabela */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuário</TableHead>
                      <TableHead>Permissão</TableHead>
                      <TableHead className="hidden md:table-cell">
                        Status
                      </TableHead>
                      <TableHead className="hidden lg:table-cell">
                        Última alteração
                      </TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading && (
                      <TableRow>
                        <TableCell
                          colSpan={5}
                          className="text-center py-10 text-muted-foreground text-sm"
                        >
                          Carregando...
                        </TableCell>
                      </TableRow>
                    )}
                    {!isLoading && filtered.length === 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={5}
                          className="text-center py-10 text-muted-foreground text-sm"
                        >
                          Nenhum usuário encontrado.
                        </TableCell>
                      </TableRow>
                    )}
                    {filtered.map((user) => {
                      const status = user.account_status || (user.is_active ? "active" : "inactive");
                      const initials = (user.name || user.full_name || user.email || "?")
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .slice(0, 2)
                        .toUpperCase();
                      return (
                        <TableRow
                          key={user.id}
                          className={status === "blocked" ? "opacity-60" : ""}
                        >
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="w-8 h-8 shrink-0">
                                <AvatarFallback className="text-xs bg-primary/10 text-primary">
                                  {initials}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="text-sm font-medium">
                                  {user.name || user.full_name || "—"}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {user.email}
                                </p>
                                {user.job_title && (
                                  <p className="text-xs text-muted-foreground">
                                    {user.job_title}
                                  </p>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`text-xs ${ROLE_COLORS[user.role] || ROLE_COLORS.operator}`}
                            >
                              {ROLE_LABELS[user.role] || user.role}
                            </Badge>
                          </TableCell>
                          <TableCell className="hidden md:table-cell">
                            <div className="space-y-1">
                              <UserStatusBadge status={status} />
                              {status === "blocked" && user.blocked_reason && (
                                <p className="text-xs text-muted-foreground max-w-[180px] truncate">
                                  {user.blocked_reason}
                                </p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="hidden lg:table-cell text-xs text-muted-foreground">
                            {user.last_changed_at ? (
                              <span>
                                {format(
                                  new Date(user.last_changed_at),
                                  "dd/MM/yy HH:mm",
                                  { locale: ptBR },
                                )}
                                <br />
                                <span className="text-muted-foreground/70">
                                  {user.last_changed_by}
                                </span>
                              </span>
                            ) : (
                              "—"
                            )}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                >
                                  <MoreHorizontal className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-52">
                                <DropdownMenuItem
                                  onClick={() => setEditUser(user)}
                                >
                                  <Pencil className="w-4 h-4 mr-2" />
                                  Editar dados
                                </DropdownMenuItem>
                                {status === "pending_invite" ? (
                                  <DropdownMenuItem
                                    disabled={resendingId === user.id}
                                    onClick={() => handleResendInvite(user)}
                                  >
                                    <MailWarning className="w-4 h-4 mr-2" />
                                    {resendingId === user.id ? "Reenviando..." : "Reenviar convite"}
                                  </DropdownMenuItem>
                                ) : (
                                  <DropdownMenuItem
                                    onClick={() => handleResetPassword(user)}
                                  >
                                    <KeyRound className="w-4 h-4 mr-2" />
                                    Redefinir senha
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuItem
                                  onClick={() => setLogUser(user)}
                                >
                                  <ClipboardList className="w-4 h-4 mr-2" />
                                  Ver histórico
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {status !== "blocked" && (
                                  <DropdownMenuItem
                                    onClick={() => handleToggleActive(user)}
                                  >
                                    {status === "active" ? (
                                      <>
                                        <UserX className="w-4 h-4 mr-2" />
                                        Desativar
                                      </>
                                    ) : (
                                      <>
                                        <UserCheck className="w-4 h-4 mr-2" />
                                        Ativar
                                      </>
                                    )}
                                  </DropdownMenuItem>
                                )}
                                {status !== "blocked" && (
                                  <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => setBlockUser(user)}
                                  >
                                    <ShieldOff className="w-4 h-4 mr-2" />
                                    Bloquear (inadimpl.)
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuItem
                                  className="text-destructive focus:text-destructive"
                                  onClick={() => handleDelete(user)}
                                >
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  Excluir usuário
                                </DropdownMenuItem>
                                {status === "blocked" && (
                                  <DropdownMenuItem
                                    onClick={() => handleUnblock(user)}
                                  >
                                    <Shield className="w-4 h-4 mr-2" />
                                    Desbloquear
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogs / Drawers */}
      {editUser && (
        <EditUserDialog
          user={editUser}
          open={!!editUser}
          onClose={() => setEditUser(null)}
          onSave={handleEdit}
        />
      )}
      {blockUser && (
        <BlockUserDialog
          user={blockUser}
          open={!!blockUser}
          onClose={() => setBlockUser(null)}
          onBlock={handleBlock}
        />
      )}
      {logUser && (
        <UserLogDrawer
          userId={logUser.id}
          userName={logUser.name || logUser.full_name || logUser.email}
          open={!!logUser}
          onClose={() => setLogUser(null)}
        />
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Plus, Tag as TagIcon } from "lucide-react";
import { tagApi, type Tag } from "../../api/tagApi";
import { ApiError } from "../../lib/apiClient";
import { Button, Card, Modal, PageHeader, TextField } from "../../components/ui";

export function AdminTags() {
  const [tags, setTags] = useState<Tag[]>([]); const [name, setName] = useState(""); const [loading, setLoading] = useState(false); const [editing, setEditing] = useState<Tag | null>(null); const [editName, setEditName] = useState("");
  const load = async () => { try { setTags(await tagApi.listAdmin()); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể tải danh mục thẻ"); } };
  useEffect(() => { load(); }, []);
  const create = async () => { if (!name.trim()) return; setLoading(true); try { await tagApi.create(name); setName(""); await load(); toast.success("Đã thêm thẻ."); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể thêm thẻ"); } finally { setLoading(false); } };
  const rename = async () => { if (!editing || !editName.trim() || editName === editing.name) { setEditing(null); return; } try { await tagApi.rename(editing.id, editName); setEditing(null); await load(); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể đổi tên thẻ"); } };
  const toggle = async (tag: Tag) => { try { await tagApi.setActive(tag.id, !tag.is_active); await load(); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể cập nhật thẻ"); } };
  return <div><PageHeader title="Quản lý thẻ" description="Danh mục thẻ chuẩn tiếng Việt dùng cho món ăn và tạo thực đơn." /><Card title="Thêm thẻ" icon={<TagIcon className="h-5 w-5" />} className="mb-5"><div className="flex gap-2"><TextField aria-label="Tên thẻ" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ví dụ: lành mạnh" className="flex-1" /><Button onClick={create} loading={loading}><Plus className="h-4 w-4" /> Thêm</Button></div></Card><Card title={`${tags.length} thẻ`} bodyClassName="p-0"><ul className="divide-y divide-sand-100">{tags.map((tag) => <li key={tag.id} className="flex items-center justify-between gap-3 px-5 py-3"><span className={tag.is_active ? "text-gray-800" : "text-gray-400 line-through"}>#{tag.name}</span><div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => { setEditing(tag); setEditName(tag.name); }}>Đổi tên</Button><Button size="sm" variant={tag.is_active ? "danger" : "secondary"} onClick={() => toggle(tag)}>{tag.is_active ? "Ngừng dùng" : "Kích hoạt"}</Button></div></li>)}</ul></Card><Modal open={!!editing} onClose={() => setEditing(null)} title="Đổi tên thẻ" size="sm" footer={<><Button variant="ghost" onClick={() => setEditing(null)}>Hủy</Button><Button onClick={rename}>Lưu</Button></>}><TextField label="Tên thẻ" value={editName} onChange={(event) => setEditName(event.target.value)} /></Modal></div>;
}

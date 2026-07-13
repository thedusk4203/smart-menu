import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { ChefHat, Leaf, Plus, Tag as TagIcon } from "lucide-react";
import { tagApi, type Tag, type TagEntityType } from "../../api/tagApi";
import { ApiError } from "../../lib/apiClient";
import { Badge, Button, Card, Modal, PageHeader, SelectField, TextField } from "../../components/ui";

const TYPE_OPTIONS = [
  { value: "dish", label: "Món ăn" },
  { value: "ingredient", label: "Nguyên liệu" },
];

const TYPE_META = {
  dish: {
    title: "Thẻ món ăn",
    description: "Dùng để mô tả món và ưu tiên khi tạo thực đơn.",
    icon: ChefHat,
    badge: "bg-brand-50 text-brand-800",
  },
  ingredient: {
    title: "Thẻ nguyên liệu",
    description: "Dùng để phân loại và tra cứu nguyên liệu nhập vào.",
    icon: Leaf,
    badge: "bg-emerald-50 text-emerald-800",
  },
} satisfies Record<TagEntityType, { title: string; description: string; icon: typeof Leaf; badge: string }>;

function TagList({
  type,
  tags,
  loading,
  onEdit,
  onToggle,
}: {
  type: TagEntityType;
  tags: Tag[];
  loading: boolean;
  onEdit: (tag: Tag) => void;
  onToggle: (tag: Tag) => void;
}) {
  const meta = TYPE_META[type];
  const Icon = meta.icon;
  return (
    <Card
      title={meta.title}
      icon={<Icon className="h-5 w-5" />}
      action={<Badge className={meta.badge}>{tags.length} thẻ</Badge>}
      bodyClassName="p-0"
    >
      <p className="border-b border-sand-100 px-5 py-3 text-sm text-gray-600">{meta.description}</p>
      {loading ? (
        <div className="space-y-3 p-5" aria-label={`Đang tải ${meta.title.toLocaleLowerCase("vi")}`}>
          {[0, 1, 2].map((item) => <div key={item} className="h-10 animate-pulse rounded-xl bg-sand-100" />)}
        </div>
      ) : tags.length === 0 ? (
        <div className="px-5 py-10 text-center">
          <Icon className="mx-auto h-8 w-8 text-gray-400" aria-hidden="true" />
          <p className="mt-3 font-medium text-gray-800">Chưa có {meta.title.toLocaleLowerCase("vi")}</p>
          <p className="mt-1 text-sm text-gray-600">Thẻ mới có thể được tạo tại đây hoặc tự động khi import.</p>
        </div>
      ) : (
        <ul className="divide-y divide-sand-100">
          {tags.map((tag) => (
            <li key={tag.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
              <div className="min-w-0">
                <p className={`truncate font-medium ${tag.is_active ? "text-gray-900" : "text-gray-500 line-through"}`}>#{tag.name}</p>
                {!tag.is_active && <p className="mt-0.5 text-xs text-gray-500">Đang ngừng dùng</p>}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => onEdit(tag)}>Đổi tên</Button>
                <Button size="sm" variant={tag.is_active ? "danger" : "secondary"} onClick={() => onToggle(tag)}>
                  {tag.is_active ? "Ngừng dùng" : "Kích hoạt"}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function AdminTags() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState<TagEntityType>("dish");
  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [editing, setEditing] = useState<Tag | null>(null);
  const [editName, setEditName] = useState("");

  const load = useCallback(async () => {
    setLoadingList(true);
    try {
      setTags(await tagApi.listAdmin());
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể tải danh mục thẻ");
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const grouped = useMemo(() => ({
    dish: tags.filter((tag) => tag.entity_type === "dish"),
    ingredient: tags.filter((tag) => tag.entity_type === "ingredient"),
  }), [tags]);

  const create = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      await tagApi.create(name, type);
      setName("");
      await load();
      toast.success(`Đã thêm thẻ ${type === "dish" ? "món ăn" : "nguyên liệu"}.`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể thêm thẻ");
    } finally {
      setLoading(false);
    }
  };

  const rename = async () => {
    if (!editing || !editName.trim() || editName === editing.name) { setEditing(null); return; }
    try {
      await tagApi.rename(editing.id, editName);
      setEditing(null);
      await load();
      toast.success("Đã đổi tên thẻ.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể đổi tên thẻ");
    }
  };

  const toggle = async (tag: Tag) => {
    try {
      await tagApi.setActive(tag.id, !tag.is_active);
      await load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể cập nhật thẻ");
    }
  };

  return (
    <div>
      <PageHeader title="Quản lý thẻ" description="Quản lý riêng thẻ nguyên liệu và thẻ món ăn; import sẽ tự bổ sung thẻ mới đúng loại." />
      <Card title="Thêm thẻ" icon={<TagIcon className="h-5 w-5" />} className="mb-5">
        <div className="grid gap-3 sm:grid-cols-[180px_minmax(0,1fr)_auto] sm:items-end">
          <SelectField
            label="Loại thẻ"
            value={type}
            options={TYPE_OPTIONS}
            onChange={(event) => setType(event.target.value as TagEntityType)}
          />
          <TextField
            label="Tên thẻ"
            value={name}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => { if (event.key === "Enter") void create(); }}
            placeholder={type === "dish" ? "Ví dụ: lành mạnh" : "Ví dụ: giàu chất xơ"}
          />
          <Button onClick={create} loading={loading} className="sm:mb-0.5"><Plus className="h-4 w-4" /> Thêm thẻ</Button>
        </div>
      </Card>
      <div className="grid items-start gap-5 xl:grid-cols-2">
        <TagList type="dish" tags={grouped.dish} loading={loadingList} onEdit={(tag) => { setEditing(tag); setEditName(tag.name); }} onToggle={toggle} />
        <TagList type="ingredient" tags={grouped.ingredient} loading={loadingList} onEdit={(tag) => { setEditing(tag); setEditName(tag.name); }} onToggle={toggle} />
      </div>
      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={`Đổi tên ${editing ? TYPE_META[editing.entity_type].title.toLocaleLowerCase("vi") : "thẻ"}`}
        size="sm"
        footer={<><Button variant="ghost" onClick={() => setEditing(null)}>Hủy</Button><Button onClick={rename}>Lưu</Button></>}
      >
        <TextField label="Tên thẻ" value={editName} onChange={(event) => setEditName(event.target.value)} />
      </Modal>
    </div>
  );
}

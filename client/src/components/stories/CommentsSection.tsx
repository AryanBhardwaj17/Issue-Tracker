"use client";

import { useState, useRef } from "react";
import { format } from "date-fns";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { useComments, useCreateComment, useUpdateComment, useDeleteComment, useUploadImage } from "@/hooks/useComments";
import type { Comment, CommentCreatePayload } from "@/lib/api";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import ImageLightbox from "@/components/ui/ImageLightbox";
import { useAuthStore } from "@/stores/authStore";
import { canEditComment, canDeleteComment } from "@/lib/auth-predicates";

interface CommentsSectionProps {
  projectId: string;
  storyId: string;
  userRole: "owner" | "member";
}

const COMMENT_MAX_LENGTH = 10000;

export default function CommentsSection({ projectId, storyId, userRole }: CommentsSectionProps) {
  const { data, isLoading } = useComments(projectId, storyId);
  const createComment = useCreateComment(projectId, storyId);
  const updateComment = useUpdateComment(projectId, storyId);
  const deleteComment = useDeleteComment(projectId, storyId);
  const uploadImage = useUploadImage();

  const [body, setBody] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; } | null>(null);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentUser = useAuthStore((s) => s.user);
  const comments = data?.items ?? [];

  const handleSubmit = () => {
    if (!body.trim()) return;
    const payload: CommentCreatePayload = { body: body.trim() };
    if (imageUrl) payload.imageUrl = imageUrl;
    createComment.mutate(payload, {
      onSuccess: () => {
        setBody("");
        setImageUrl(null);
      },
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadImage.mutate(file, {
      onSuccess: (url) => setImageUrl(url),
    });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleEditSave = (commentId: string) => {
    if (!editBody.trim()) return;
    updateComment.mutate({ commentId, body: { body: editBody.trim() } }, {
      onSuccess: () => {
        setEditingId(null);
        setEditBody("");
      },
    });
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteComment.mutate(deleteTarget.id, {
      onSuccess: () => setDeleteTarget(null),
    });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-900">
          Comments {comments.length > 0 && <span className="font-normal text-gray-400">({comments.length})</span>}
        </h3>
      </div>

      {/* Comments list */}
      <div className="divide-y divide-gray-50">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-gray-600" />
          </div>
        )}

        {!isLoading && comments.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            No comments yet. Be the first to comment.
          </div>
        )}

        {comments.map((comment) => (
          <CommentItem
            key={comment.id}
            comment={comment}
            currentUserId={currentUser?.id ?? ""}
            userRole={userRole}
            isEditing={editingId === comment.id}
            editBody={editBody}
            onEditStart={() => { setEditingId(comment.id); setEditBody(comment.body); }}
            onEditChange={setEditBody}
            onEditSave={() => handleEditSave(comment.id)}
            onEditCancel={() => setEditingId(null)}
            onDelete={() => setDeleteTarget({ id: comment.id })}
            onImageClick={(src) => setLightboxSrc(src)}
            isUpdating={updateComment.isPending}
          />
        ))}
      </div>

      {/* Composer */}
      <div className="border-t border-gray-100 p-4">
        <div className="relative">
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write a comment..."
            rows={3}
            maxLength={COMMENT_MAX_LENGTH}
            className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(); }}
          />
          <span className="absolute bottom-2 right-3 text-xs text-gray-400">
            {body.length}/{COMMENT_MAX_LENGTH}
          </span>
        </div>

        {imageUrl && (
          <div className="mt-2 flex items-center gap-2">
            <img src={imageUrl} alt="Attached" className="h-12 w-12 rounded object-cover" />
            <button
              onClick={() => setImageUrl(null)}
              className="text-xs text-red-500 hover:underline"
            >
              Remove
            </button>
            {!body.trim() && (
              <span className="text-xs text-amber-600">Add text to post with image</span>
            )}
          </div>
        )}

        <div className="mt-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadImage.isPending}
              className="text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50"
            >
              {uploadImage.isPending ? "Uploading..." : "📎 Attach image"}
            </button>
            <span className="text-xs text-gray-400">Ctrl+Enter to submit</span>
          </div>
          <Button
            variant="primary"
            onClick={handleSubmit}
            isLoading={createComment.isPending}
            disabled={!body.trim()}
            className="!px-4 !py-1.5 text-xs"
          >
            Comment
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Comment"
        message="Are you sure you want to delete this comment?"
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteComment.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      {lightboxSrc && (
        <ImageLightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />
      )}
    </div>
  );
}

// ── Comment Item ──────────────────────────────────────────────────────────────

interface CommentItemProps {
  comment: Comment;
  currentUserId: string;
  userRole: "owner" | "member";
  isEditing: boolean;
  editBody: string;
  onEditStart: () => void;
  onEditChange: (v: string) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onDelete: () => void;
  onImageClick: (src: string) => void;
  isUpdating: boolean;
}

function CommentItem({
  comment,
  currentUserId,
  userRole,
  isEditing,
  editBody,
  onEditStart,
  onEditChange,
  onEditSave,
  onEditCancel,
  onDelete,
  onImageClick,
  isUpdating,
}: CommentItemProps) {
  const canEdit = canEditComment(comment, currentUserId);
  const canDelete = canDeleteComment(comment, currentUserId, userRole);
  const isOwn = comment.author.id === currentUserId;
  const isEdited = new Date(comment.updatedAt).getTime() > new Date(comment.createdAt).getTime();

  return (
    <div className={`px-4 py-3 ${isOwn ? "bg-blue-50/50" : ""}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-200 text-xs font-medium text-gray-600">
            {comment.author.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <span className="text-sm font-medium text-gray-900">{comment.author.name}</span>
            <span className="ml-2 text-xs text-gray-400">
              {format(new Date(comment.createdAt), "MMM d, yyyy 'at' h:mm a")}
            </span>
            {isEdited && (
              <span className="ml-1 text-xs text-gray-400">(edited)</span>
            )}
          </div>
        </div>
        {(canEdit || canDelete) && !isEditing && (
          <div className="flex items-center gap-1">
            {canEdit && (
              <button
                onClick={onEditStart}
                className="rounded p-1 text-xs text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                Edit
              </button>
            )}
            {canDelete && (
              <button
                onClick={onDelete}
                className="rounded p-1 text-xs text-gray-400 hover:bg-red-50 hover:text-red-600"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>

      <div className="ml-9 mt-1">
        {isEditing ? (
          <div>
            <textarea
              value={editBody}
              onChange={(e) => onEditChange(e.target.value)}
              rows={3}
              maxLength={COMMENT_MAX_LENGTH}
              className="w-full resize-none rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
              onKeyDown={(e) => { if (e.key === "Escape") onEditCancel(); if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); onEditSave(); } }}
            />
            <div className="mt-1 flex items-center gap-2">
              <Button variant="primary" onClick={onEditSave} isLoading={isUpdating} className="!px-3 !py-1 text-xs">
                Save
              </Button>
              <Button variant="secondary" onClick={onEditCancel} className="!px-3 !py-1 text-xs">
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="prose prose-sm max-w-none text-gray-700">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
                {comment.body}
              </ReactMarkdown>
            </div>
            {comment.imageUrl && (
              <img
                src={comment.imageUrl}
                alt="Comment attachment"
                className="mt-2 max-h-48 cursor-pointer rounded-lg object-cover hover:opacity-90"
                onClick={() => onImageClick(comment.imageUrl!)}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

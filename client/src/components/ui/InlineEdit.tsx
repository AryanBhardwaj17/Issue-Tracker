"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";

interface InlineEditProps {
  value: string;
  onSave: (newValue: string) => void;
  placeholder?: string;
  as?: "input" | "textarea";
  maxLength?: number;
  className?: string;
  inputClassName?: string;
  disabled?: boolean;
}

export default function InlineEdit({
  value,
  onSave,
  placeholder = "Click to edit",
  as = "input",
  maxLength,
  className = "",
  inputClassName = "",
  disabled = false,
}: InlineEditProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const handleSave = () => {
    const trimmed = draft.trim();
    if (trimmed && trimmed !== value) {
      onSave(trimmed);
    } else {
      setDraft(value);
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setDraft(value);
    setEditing(false);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && as === "input") {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  if (disabled || !editing) {
    return (
      <span
        className={`cursor-pointer rounded px-1 py-0.5 hover:bg-gray-100 ${!value ? "text-gray-400 italic" : ""} ${className}`}
        onClick={() => !disabled && setEditing(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setEditing(true); } }}
      >
        {value || placeholder}
      </span>
    );
  }

  const commonProps = {
    ref: inputRef as never,
    value: draft,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setDraft(e.target.value),
    onBlur: handleSave,
    onKeyDown: handleKeyDown,
    maxLength,
    className: `w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 ${inputClassName}`,
  };

  if (as === "textarea") {
    return (
      <div className="relative">
        <textarea rows={3} {...commonProps} />
        <div className="mt-1 flex items-center justify-between">
          <span className="text-xs text-gray-400">Esc to cancel</span>
          {maxLength && (
            <span className="text-xs text-gray-400">
              {draft.length}/{maxLength}
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <input type="text" {...commonProps} />
      <p className="mt-1 text-xs text-gray-400">Enter to save · Esc to cancel</p>
    </div>
  );
}

"use client";

interface CheckboxProps {
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
  title?: string;
}

/**
 * Styled checkbox that calls stopPropagation to prevent
 * row-click handlers from firing when toggling.
 */
export default function Checkbox({
  checked,
  disabled = false,
  onChange,
  title,
}: CheckboxProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      title={title}
      onClick={(e) => {
        e.stopPropagation();
        if (!disabled) onChange(!checked);
      }}
      className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1 ${
        checked
          ? "border-gray-900 bg-gray-900 text-white"
          : "border-gray-300 bg-white"
      } ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:border-gray-500"}`}
    >
      {checked && (
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
  );
}

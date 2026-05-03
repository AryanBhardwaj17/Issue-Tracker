"use client";

import { useRef, useState } from "react";

interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

/**
 * Debounced search input (300 ms).
 * Shows the local value immediately while waiting to call onChange.
 * Syncs back if the external value changes (e.g. filter reset).
 */
export default function SearchBox({
  value,
  onChange,
  placeholder = "Search stories...",
}: SearchBoxProps) {
  const [local, setLocal] = useState(value);
  const [prevValue, setPrevValue] = useState(value);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Derived state: sync when external value changes (e.g. filter reset).
  // setState during render is the React-approved pattern over useEffect here.
  if (prevValue !== value) {
    setPrevValue(value);
    setLocal(value);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setLocal(v);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => onChange(v), 300);
  }

  return (
    <input
      type="text"
      value={local}
      onChange={handleChange}
      placeholder={placeholder}
      className="min-w-[200px] rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
    />
  );
}

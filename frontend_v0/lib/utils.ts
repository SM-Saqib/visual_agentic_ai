import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { formatDistanceToNow as formatDistance } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDistanceToNow(date: Date | string) {
  const dateObj = typeof date === "string" ? new Date(date) : date
  return formatDistance(dateObj, { addSuffix: true })
}

import axios from "axios";

export function extractErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Network error. Please try again";
    }

    const data = error.response.data;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (typeof data?.message === "string") {
      return data.message;
    }

    return fallback;
  }

  return "Something went wrong";
}

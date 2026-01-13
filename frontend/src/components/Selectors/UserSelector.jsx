import { useEffect, useState } from "react";
import { Dropdown } from "primereact/dropdown";

import {
  getUsersForCurrentCase,
  getCriminologists,
  getAllUsers
} from "../../services/assigneeService";

/**
 * Reusable user selector
 *
 * Props:
 * - value: selected userId
 * - onChange: function(userId)
 * - assignerStatus: "coworker" | "leader" | "admin"
 * - placeholder (optional)
 * - disabled (optional)
 */
export default function UserSelector({
  value,
  onChange,
  assignerStatus,
  placeholder = "Select a user",
  disabled = false
}) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadUsers();
    // reload if status changes
  }, [assignerStatus]);

  const loadUsers = async () => {
    if (!assignerStatus) return;

    setLoading(true);
    try {
      let response;

      switch (assignerStatus) {
        case "coworker":
          response = await getUsersForCurrentCase();
          break;

        case "leader":
          response = await getCriminologists();
          break;

        case "admin":
          response = await getAllUsers();
          break;

        default:
          console.warn("Unknown assignerStatus:", assignerStatus);
          return;
      }

      setUsers(response.data);

    } catch (err) {
      console.error("Failed to load users", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dropdown
      value={value}
      options={users}
      optionLabel="username"
      optionValue="userId"
      onChange={(e) => onChange(e.value)}
      placeholder={placeholder}
      loading={loading}
      disabled={disabled || !assignerStatus}
      showClear
      filter
      className="w-full"
    />
  );
}

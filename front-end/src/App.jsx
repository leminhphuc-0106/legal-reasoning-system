
import { useMemo, useRef, useState } from "react";
import "./App.css";

const initialCriteria = [
  {
    id: "TC01",
    name: "Đối tượng và điều kiện xét khen thưởng",
    description: "Kiểm tra đối tượng có thuộc phạm vi áp dụng của quy định hay không.",
    legalBasis: "Căn cứ văn bản pháp luật đã tải lên",
  },
  {
    id: "TC02",
    name: "Thành tích công tác",
    description: "Đánh giá thành tích và kết quả thực hiện nhiệm vụ.",
    legalBasis: "Căn cứ tiêu chuẩn xét khen thưởng",
  },
  {
    id: "TC03",
    name: "Chấp hành chủ trương, quy định",
    description: "Kiểm tra việc chấp hành quy định trong quá trình công tác.",
    legalBasis: "Căn cứ quy định liên quan",
  },
  {
    id: "TC04",
    name: "Minh chứng và hồ sơ hợp lệ",
    description: "Kiểm tra tính đầy đủ, hợp lệ của các tài liệu minh chứng.",
    legalBasis: "Căn cứ thành phần hồ sơ",
  },
];

const initialCandidates = [
  {
    id: "HS001",
    name: "Nguyễn Văn An",
    position: "Chuyên viên công nghệ thông tin",
    department: "Phòng Công nghệ thông tin",
    submittedAt: "29/10/2026",
    awardType: "Đề nghị xét khen thưởng",
    summary:
      "Hồ sơ có thông tin thành tích công tác. Cần đối chiếu các minh chứng với tiêu chuẩn áp dụng trước khi kết luận.",
    criteriaResults: [
      {
        criterionId: "TC01",
        status: "pass",
        reason: "Thông tin đối tượng đã được cung cấp.",
        evidence: "Thông tin trong hồ sơ ứng viên",
      },
      {
        criterionId: "TC02",
        status: "pass",
        reason: "Hồ sơ có thông tin về thành tích công tác.",
        evidence: "Bản kê khai thành tích",
      },
      {
        criterionId: "TC03",
        status: "pending",
        reason: "Chưa có đủ tài liệu để xác minh.",
        evidence: "Chưa có minh chứng",
      },
      {
        criterionId: "TC04",
        status: "fail",
        reason: "Cần bổ sung tài liệu minh chứng còn thiếu.",
        evidence: "Chưa cung cấp đầy đủ",
      },
    ],
  },
  {
    id: "HS002",
    name: "Trần Thị Bình",
    position: "Chuyên viên hành chính",
    department: "Phòng Tổ chức - Hành chính",
    submittedAt: "28/10/2026",
    awardType: "Đề nghị xét khen thưởng",
    summary: "Hồ sơ cần được đối chiếu với các tiêu chuẩn và tài liệu minh chứng.",
    criteriaResults: [],
  },
];

function normalizeStatus(status) {
  const value = String(status ?? "").trim().toLowerCase();

  if (
    ["pass", "passed", "đạt", "đạt tiêu chí", "true", "yes"].includes(value)
  ) {
    return "pass";
  }

  if (
    ["fail", "failed", "chưa đạt", "không đạt", "false", "no"].includes(value)
  ) {
    return "fail";
  }

  return "pending";
}

function normalizeCriteria(data) {
  const items = Array.isArray(data)
    ? data
    : data?.criteria ?? data?.criterias ?? data?.tieu_chi;

  if (!Array.isArray(items)) {
    throw new Error("Không tìm thấy mảng criteria trong file JSON.");
  }

  return items.map((item, index) => ({
    id: String(item.id ?? item.code ?? `TC${index + 1}`),
    name: item.name ?? item.ten_tieu_chi ?? item.title ?? `Tiêu chí ${index + 1}`,
    description:
      item.description ?? item.mo_ta ?? item.requirement ?? "Chưa có mô tả.",
    legalBasis:
      item.legalBasis ?? item.can_cu_phap_ly ?? item.legal_basis ?? "",
    required: item.required ?? item.bat_buoc ?? true,
  }));
}

function normalizeCandidate(item, index) {
  const rawResults =
    item.criteriaResults ??
    item.criteria_results ??
    item.results ??
    item.ket_qua_tieu_chi ??
    [];

  const results = Array.isArray(rawResults)
    ? rawResults
    : Object.entries(rawResults).map(([criterionId, value]) => ({
        criterionId,
        ...(typeof value === "object" ? value : { status: value }),
      }));

  return {
    id: String(
      item.id ?? item.ma_ho_so ?? item.candidateId ?? `HS${index + 1}`
    ),
    name: item.name ?? item.ho_ten ?? item.full_name ?? `Ứng viên ${index + 1}`,
    position:
      item.position ?? item.vi_tri ?? item.chuc_vu ?? "Chưa cập nhật",
    department:
      item.department ?? item.don_vi ?? item.phong_ban ?? "Chưa cập nhật",
    submittedAt:
      item.submittedAt ?? item.ngay_nop ?? item.submitted_at ?? "Chưa cập nhật",
    awardType:
      item.awardType ?? item.hinh_thuc_khen_thuong ?? "Chưa xác định",
    summary:
      item.summary ?? item.tom_tat ?? item.nhan_xet ?? "Chưa có nhận xét.",
    criteriaResults: results.map((result) => ({
      criterionId: String(
        result.criterionId ?? result.criterion_id ?? result.id ?? result.ma_tieu_chi ?? ""
      ),
      status: normalizeStatus(
        result.status ?? result.trang_thai ?? result.result
      ),
      reason: result.reason ?? result.ly_do ?? result.explanation ?? "",
      evidence: result.evidence ?? result.minh_chung ?? "",
    })),
  };
}

function Icon({ children }) {
  return <span className="icon" aria-hidden="true">{children}</span>;
}

export default function App() {
  const criteriaInput = useRef(null);
  const lawInput = useRef(null);
  const candidateInput = useRef(null);

  const [criteria, setCriteria] = useState(initialCriteria);
  const [candidates, setCandidates] = useState(initialCandidates);
  const [selectedId, setSelectedId] = useState("HS001");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Xin chào! Tôi có thể hỗ trợ tra cứu quy định, đối chiếu tiêu chí và tổng hợp thông tin hồ sơ ứng viên. Hãy chọn một ứng viên ở bên phải hoặc nhập câu hỏi bên dưới.",
    },
  ]);
  const [lawFiles, setLawFiles] = useState([]);
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const selectedCandidate =
    candidates.find((item) => item.id === selectedId) ?? candidates[0];

  const results = useMemo(() => {
    if (!selectedCandidate) return [];

    return criteria.map((criterion) => {
      const result = selectedCandidate.criteriaResults.find(
        (item) => item.criterionId === criterion.id
      );

      return {
        ...criterion,
        status: result?.status ?? "pending",
        reason: result?.reason || "Chưa có kết quả đối chiếu cho tiêu chí này.",
        evidence: result?.evidence || "Chưa có minh chứng được ghi nhận.",
      };
    });
  }, [criteria, selectedCandidate]);

  const counts = {
    pass: results.filter((item) => item.status === "pass").length,
    fail: results.filter((item) => item.status === "fail").length,
    pending: results.filter((item) => item.status === "pending").length,
  };

  const percentage = results.length
    ? Math.round((counts.pass / results.length) * 100)
    : 0;

  const visibleResults = results.filter(
    (item) => filter === "all" || item.status === filter
  );

  async function readJsonFile(file) {
    const text = await file.text();
    return JSON.parse(text.replace(/^\uFEFF/, ""));
  }

  async function handleCriteriaUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const data = await readJsonFile(file);
      const nextCriteria = normalizeCriteria(data);

      setCriteria(nextCriteria);
      setNotice(`Đã nạp ${nextCriteria.length} tiêu chí từ ${file.name}.`);
    } catch (error) {
      setNotice(`Không đọc được file tiêu chí: ${error.message}`);
    }

    event.target.value = "";
  }

  async function handleLawUpload(event) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    setLawFiles((previous) => [
      ...previous,
      ...files.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type || "Không xác định",
      })),
    ]);

    setNotice(
      `Đã thêm ${files.length} tài liệu pháp luật vào danh sách.`
    );
    event.target.value = "";
  }

  async function handleCandidateUpload(event) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    setIsLoading(true);

    try {
      const jsonFiles = files.filter((file) =>
        file.name.toLowerCase().endsWith(".json")
      );

      if (!jsonFiles.length) {
        throw new Error("Vui lòng chọn ít nhất một file JSON hồ sơ.");
      }

      const parsed = await Promise.all(
        jsonFiles.map(async (file) => ({
          fileName: file.name,
          data: await readJsonFile(file),
        }))
      );

      const loaded = [];

      parsed.forEach(({ fileName, data }) => {
        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.candidates)
            ? data.candidates
            : Array.isArray(data?.ung_vien)
              ? data.ung_vien
              : [data];

        items.forEach((item, index) => {
          const candidate = normalizeCandidate(item, loaded.length + index);
          loaded.push({
            ...candidate,
            id:
              candidate.id && !loaded.some((c) => c.id === candidate.id)
                ? candidate.id
                : `${candidate.id}-${loaded.length + 1}`,
            sourceFile: fileName,
          });
        });
      });

      if (!loaded.length) throw new Error("Không tìm thấy hồ sơ hợp lệ.");

      setCandidates((previous) => {
        const byId = new Map(previous.map((item) => [item.id, item]));

        loaded.forEach((item) => byId.set(item.id, item));

        return Array.from(byId.values());
      });

      setSelectedId(loaded[0].id);
      setFilter("all");
      setNotice(`Đã đọc ${loaded.length} hồ sơ từ ${jsonFiles.length} file JSON.`);
    } catch (error) {
      setNotice(`Không đọc được hồ sơ: ${error.message}`);
    } finally {
      setIsLoading(false);
      event.target.value = "";
    }
  }

  function sendMessage(event) {
    event.preventDefault();

    const content = query.trim();
    if (!content) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content },
      {
        role: "assistant",
        content:
          "Giao diện hiện đã nhận câu hỏi. Để trả lời dựa trên văn bản pháp luật, phân tích nội dung hồ sơ và suy luận theo quy định thực tế, bạn cần kết nối chatbot này với API backend của hệ thống.",
      },
    ]);
    setQuery("");
  }

  function resetApp() {
    setCriteria(initialCriteria);
    setCandidates(initialCandidates);
    setSelectedId("HS001");
    setFilter("all");
    setLawFiles([]);
    setNotice("Đã khôi phục dữ liệu minh họa ban đầu.");
    setMessages([
      {
        role: "assistant",
        content:
          "Xin chào! Tôi có thể hỗ trợ tra cứu quy định, đối chiếu tiêu chí và tổng hợp thông tin hồ sơ ứng viên. Hãy chọn một ứng viên ở bên phải hoặc nhập câu hỏi bên dưới.",
      },
    ]);
  }

  function exportReport() {
    window.print();
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Icon>⚖</Icon></div>
          <div>
            <h1>Hệ thống hỗ trợ ra quyết định khen thưởng hành chính</h1>
            <p>Trợ lý tra cứu pháp luật và đối chiếu hồ sơ ứng viên</p>
          </div>
          <span className="version">v1.0</span>
        </div>

        <div className="top-actions">
          <span className="system-status">
            <span className="status-dot" />
            Giao diện sẵn sàng
          </span>
          <button className="button button-secondary" onClick={resetApp}>
            ↻ Đặt lại
          </button>
        </div>
      </header>

      <main className="workspace">
        <section className="chat-panel">
          <div className="chat-intro">
            <div className="intro-symbol">✳</div>
            <p className="eyebrow">TRỢ LÝ HÀNH CHÍNH SỐ</p>
            <h2>Xin chào, tôi có thể giúp gì?</h2>
            <p className="intro-description">
              Tra cứu quy định khen thưởng, kiểm tra điều kiện và tổng hợp
              thông tin hồ sơ ứng viên trên cùng một giao diện.
            </p>
          </div>

          <div className="conversation">
            {messages.map((message, index) => (
              <div
                className={`message-row ${message.role === "user" ? "message-user" : ""}`}
                key={`${message.role}-${index}`}
              >
                {message.role === "assistant" && (
                  <div className="avatar avatar-ai">AI</div>
                )}
                <div className={`message-bubble ${message.role}`}>
                  {message.content}
                </div>
                {message.role === "user" && (
                  <div className="avatar avatar-user">Bạn</div>
                )}
              </div>
            ))}

            {notice && <div className="notice"><Icon>ℹ</Icon>{notice}</div>}
          </div>

          <div className="chat-composer">
            <form onSubmit={sendMessage}>
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Nhập câu hỏi về quy định hoặc hồ sơ ứng viên..."
                rows={2}
                aria-label="Nhập câu hỏi"
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form.requestSubmit();
                  }
                }}
              />
              <div className="composer-bottom">
                <span className="composer-hint">Enter để gửi · Shift + Enter xuống dòng</span>
                <button
                  type="submit"
                  className="send-button"
                  disabled={!query.trim()}
                  aria-label="Gửi câu hỏi"
                >
                  ↑
                </button>
              </div>
            </form>
          </div>
        </section>

        <section className="results-panel">
          <div className="results-heading">
            <div>
              <p className="eyebrow">TRUNG TÂM ĐÁNH GIÁ</p>
              <h2><Icon>▤</Icon> Kết quả đối chiếu hồ sơ</h2>
              <p className="section-subtitle">
                Tổng hợp tiêu chí và minh chứng theo dữ liệu đã cung cấp
              </p>
            </div>
            <button className="button button-secondary export-button" onClick={exportReport}>
              <Icon>⇩</Icon> Xuất báo cáo
            </button>
          </div>

          <div className="upload-toolbar">
            <div className="upload-toolbar-title">
              <Icon>▣</Icon>
              <div>
                <strong>Nguồn dữ liệu</strong>
                <span>Quản lý văn bản và hồ sơ đầu vào</span>
              </div>
            </div>

            <div className="upload-actions">
              <button
                className="button button-outline"
                onClick={() => criteriaInput.current?.click()}
              >
                <Icon>▤</Icon> Nạp tiêu chí JSON
              </button>
              <button
                className="button button-outline"
                onClick={() => lawInput.current?.click()}
              >
                <Icon>＋</Icon> Thêm văn bản luật
              </button>
              <button
                className="button button-primary"
                onClick={() => candidateInput.current?.click()}
                disabled={isLoading}
              >
                <Icon>＋</Icon> Thêm hồ sơ
              </button>
            </div>

            <input
              ref={criteriaInput}
              type="file"
              accept=".json,application/json"
              hidden
              onChange={handleCriteriaUpload}
            />
            <input
              ref={lawInput}
              type="file"
              accept=".pdf,.doc,.docx,.txt,.json"
              multiple
              hidden
              onChange={handleLawUpload}
            />
            <input
              ref={candidateInput}
              type="file"
              accept=".json,application/json"
              multiple
              hidden
              onChange={handleCandidateUpload}
              {...{ webkitdirectory: "", directory: "" }}
            />
          </div>

          {lawFiles.length > 0 && (
            <div className="law-files">
              <div className="law-files-heading">
                <strong><Icon>▧</Icon> Văn bản đã thêm ({lawFiles.length})</strong>
                <button
                  className="text-button"
                  onClick={() => setLawFiles([])}
                >
                  Xóa danh sách
                </button>
              </div>
              <div className="file-chips">
                {lawFiles.map((file, index) => (
                  <span className="file-chip" key={`${file.name}-${index}`}>
                    <Icon>▤</Icon> {file.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="candidate-toolbar">
            <label htmlFor="candidate-select">
              <Icon>♙</Icon> Hồ sơ đang xem
            </label>
            <select
              id="candidate-select"
              value={selectedCandidate?.id ?? ""}
              onChange={(event) => {
                setSelectedId(event.target.value);
                setFilter("all");
              }}
            >
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.name} — {candidate.id}
                </option>
              ))}
            </select>
            <span className="candidate-count">{candidates.length} hồ sơ</span>
          </div>

          {selectedCandidate ? (
            <>
              <article className="overview-card">
                <div className="candidate-avatar">
                  {selectedCandidate.name
                    .split(" ")
                    .slice(-2)
                    .map((part) => part[0])
                    .join("")
                    .toUpperCase()}
                </div>

                <div className="candidate-main">
                  <div className="candidate-name-row">
                    <h3>{selectedCandidate.name}</h3>
                    <span className="candidate-id">{selectedCandidate.id}</span>
                  </div>
                  <p className="candidate-position">{selectedCandidate.position}</p>
                  <div className="candidate-meta">
                    <span><Icon>▦</Icon> {selectedCandidate.department}</span>
                    <span><Icon>◷</Icon> Ngày nộp: {selectedCandidate.submittedAt}</span>
                  </div>
                  <div className="candidate-meta">
                    <span><Icon>▤</Icon> {selectedCandidate.awardType}</span>
                    {selectedCandidate.sourceFile && (
                      <span><Icon>▧</Icon> {selectedCandidate.sourceFile}</span>
                    )}
                  </div>
                </div>
              </article>

              <article className="summary-card">
                <div className="summary-header">
                  <div>
                    <p className="eyebrow">TỔNG QUAN ĐÁNH GIÁ</p>
                    <h3>Mức độ đáp ứng tiêu chí</h3>
                  </div>
                  <div className="score">
                    <strong>{percentage}%</strong>
                    <span>Đạt tiêu chí</span>
                  </div>
                </div>

                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${percentage}%` }}
                  />
                </div>

                <div className="summary-stats">
                  <div className="stat-item">
                    <span className="stat-dot pass-dot" />
                    <div><strong>{counts.pass}</strong><span>Đạt</span></div>
                  </div>
                  <div className="stat-item">
                    <span className="stat-dot fail-dot" />
                    <div><strong>{counts.fail}</strong><span>Chưa đạt</span></div>
                  </div>
                  <div className="stat-item">
                    <span className="stat-dot pending-dot" />
                    <div><strong>{counts.pending}</strong><span>Chưa đủ dữ liệu</span></div>
                  </div>
                </div>

                <p className="summary-note">{selectedCandidate.summary}</p>
              </article>

              <div className="criteria-heading">
                <div>
                  <h3><Icon>☷</Icon> Chi tiết tiêu chí</h3>
                  <p>Đối chiếu từng điều kiện và minh chứng liên quan</p>
                </div>
                <div className="filter-tabs">
                  {[
                    ["all", `Tất cả (${results.length})`],
                    ["pass", `Đạt (${counts.pass})`],
                    ["fail", `Chưa đạt (${counts.fail})`],
                    ["pending", `Chưa rõ (${counts.pending})`],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      className={`filter-tab ${filter === value ? "active" : ""} ${value}`}
                      onClick={() => setFilter(value)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="criteria-list">
                {visibleResults.map((item, index) => (
                  <article
                    className={`criterion-card ${item.status}`}
                    key={item.id}
                  >
                    <div className="criterion-top">
                      <div className="criterion-title">
                        <span className="criterion-number">{index + 1}</span>
                        <h4>{item.name}</h4>
                      </div>
                      <span className={`status-badge ${item.status}`}>
                        {item.status === "pass"
                          ? "✓ ĐẠT"
                          : item.status === "fail"
                            ? "× CHƯA ĐẠT"
                            : "◷ CHƯA ĐỦ DỮ LIỆU"}
                      </span>
                    </div>

                    <p className="criterion-description">{item.description}</p>
                    <p className="criterion-reason">{item.reason}</p>

                    <div className="criterion-footer">
                      <span><Icon>▧</Icon> Minh chứng: {item.evidence}</span>
                      {item.legalBasis && (
                        <span className="legal-basis">
                          Căn cứ: {item.legalBasis}
                        </span>
                      )}
                    </div>
                  </article>
                ))}

                {visibleResults.length === 0 && (
                  <div className="empty-state">
                    Không có tiêu chí nào thuộc trạng thái đang chọn.
                  </div>
                )}
              </div>

              <div className="disclaimer">
                <Icon>ⓘ</Icon>
                <p>
                  <strong>Lưu ý:</strong> Kết quả hiển thị phụ thuộc vào dữ liệu
                  đầu vào. Tỷ lệ đạt chỉ là thống kê tiêu chí, không tự động
                  thay thế kết luận pháp lý hoặc quyết định của người có thẩm quyền.
                </p>
              </div>
            </>
          ) : (
            <div className="empty-state">
              Chưa có hồ sơ. Hãy tải lên file JSON ứng viên để bắt đầu.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

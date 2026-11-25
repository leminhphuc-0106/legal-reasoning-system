// App.jsx
// Thành phần gốc của ứng dụng: quản lý trạng thái dữ liệu và điều phối các khu vực giao diện.
import { useRef, useState } from "react";
import MainLayout from "./layouts/MainLayout.jsx";
import DataUpload from "./components/upload/DataUpload.jsx";
import ResultsHeading from "./components/evaluation/ResultsHeading.jsx";
import EvaluationPanel from "./components/evaluation/EvaluationPanel.jsx";
import { askAssistant } from "./services/chatService.js";
import { evaluateCandidates, generateReport } from "./services/evalService.js";
import "./styles/App.css";

// Tin nhắn chào mừng mặc định của trợ lý khi mở ứng dụng.
const welcomeMessage = `Xin chào! Tôi có thể hỗ trợ được gì cho bạn ?`;

export default function App() {
  // Các ref trỏ tới input file ẩn dùng để mở hộp chọn tệp và thư mục.
  const lawInput = useRef(null);
  const candidateFileInput = useRef(null);
  const candidateFolderInput = useRef(null);

  // Trạng thái danh sách hồ sơ ứng viên nhận từ kết quả xét.
  const [candidates, setCandidates] = useState([]);

  // Hồ sơ đang được chọn và bộ lọc trạng thái tiêu chí (all/pass/fail/pending).
  const [selectedId, setSelectedId] = useState("HS01");
  const [filter, setFilter] = useState("all");

  // Nội dung câu hỏi đang nhập và lịch sử hội thoại với trợ lý.
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([{ role: "assistant", content: welcomeMessage }]);

  // Danh sách tài liệu pháp luật, hồ sơ chờ xét và thông báo trạng thái gần nhất.
  const [lawFiles, setLawFiles] = useState([]);
  const [candidateFiles, setCandidateFiles] = useState([]);
  const [notice, setNotice] = useState("");

  // Cờ báo đang xử lý khi gửi dữ liệu lên hệ thống.
  const [isLoading, setIsLoading] = useState(false);

  // Xử lí chọn và kiểm tra file PDF văn bản pháp luật.
  function handleLawUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    // Chỉ chấp nhận tài liệu pháp luật dạng PDF.
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setNotice("Vui lòng chỉ chọn file PDF.");
      event.target.value = "";
      return;
    }

    setLawFiles([file]);
    setNotice(`Đã thêm tài liệu pháp luật: ${file.name}`);
    event.target.value = "";
  }

  // Xử lí thêm một hoặc nhiều file hồ sơ ứng viên vào danh sách chờ xét.
  function handleCandidateUpload(event) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    setCandidateFiles(previous => [...previous, ...files]);
    event.target.value = "";
  }

  // Xử lí gửi dữ liệu lên backend và hiển thị kết quả xét hồ sơ.
  async function handleEvaluate() {
    try {
      setIsLoading(true);
      setNotice("Đang gửi hồ sơ lên hệ thống...");

      // Kiểm tra dữ liệu đầu vào trước khi gửi.
      if (!lawFiles.length) {
        throw new Error("Vui lòng chọn file PDF tiêu chí xét thưởng.");
      }
      if (!candidateFiles.length) {
        throw new Error("Vui lòng thêm hồ sơ ứng viên.");
      }

      // Đóng gói file tiêu chí và toàn bộ hồ sơ ứng viên vào FormData.
      const formData = new FormData();
      formData.append("criteria_file", lawFiles[0]);
      candidateFiles.forEach(file => formData.append("candidate_files", file));

      // Gọi API đánh giá hồ sơ bằng Knowledge Graph.
      const result = await evaluateCandidates(formData);
      setCandidates(result.candidates || []);
      if (result.candidates?.length > 0) {
        setSelectedId(result.candidates[0].id);
      }

      setNotice("Đang sử dụng Qwen để phân tích và sinh báo cáo...");

      // Gọi API sinh báo cáo tổng hợp bằng Qwen.
      const reportResult = await generateReport(result.candidates);
      const combinedReport = (reportResult.results || []).join("\n\n");
      setMessages(previous => [
        ...previous,
        { role: "assistant", content: combinedReport }
      ]);
      setNotice("Đã hoàn tất xét hồ sơ và sinh báo cáo!");
    } catch (error) {
      console.error("Lỗi xét hồ sơ:", error);
      setNotice(`Lỗi: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }

  // Xử lí gửi câu hỏi của người dùng tới trợ lý.
  async function sendMessage(event) {
    event.preventDefault();
    const content = query.trim();
    if (!content) return;

    // Lưu lịch sử trước khi thêm câu hỏi mới để gửi kèm ngữ cảnh cho trợ lý.
    const history = messages.map(({ role, content }) => ({ role, content }));

    // Chỉ gửi thông tin tóm tắt của hồ sơ để giữ payload chat gọn nhẹ.
    const candidateContext = candidates.map(({ id, name, coverage }) => ({ id, name, coverage }));

    setMessages(previous => [...previous, { role: "user", content }]);
    setQuery("");
    setNotice("Trợ lý đang soạn câu trả lời...");

    try {
      const answer = await askAssistant(content, { history, candidates: candidateContext });
      setMessages(previous => [...previous, { role: "assistant", content: answer }]);
      setNotice("");
    } catch (error) {
      setMessages(previous => [...previous, {
        role: "assistant",
        content: error.message || "Không thể kết nối backend lúc này.",
      }]);
      setNotice("");
    }
  }

  // Xử lí khôi phục hội thoại và trạng thái ban đầu.
  function resetApp() {
    setSelectedId("HS01");
    setFilter("all");
    setNotice("Đã khôi phục dữ liệu minh họa ban đầu.");
    setMessages([{ role: "assistant", content: welcomeMessage }]);
    setQuery("");
  }

  return <MainLayout
    onReset={resetApp}
    chatProps={{ messages, notice, query, setQuery, onSend: sendMessage }}
  >
    <ResultsHeading />

    <DataUpload
      lawInput={lawInput}
      candidateFileInput={candidateFileInput}
      candidateFolderInput={candidateFolderInput}
      onLawUpload={handleLawUpload}
      onCandidateUpload={handleCandidateUpload}
      onEvaluate={handleEvaluate}
      isLoading={isLoading}
      lawFiles={lawFiles}
      onClearLawFiles={() => setLawFiles([])}
      candidateFiles={candidateFiles}
      onClearCandidateFiles={() => setCandidateFiles([])}
    />

    <EvaluationPanel
      candidates={candidates}
      selectedId={selectedId}
      onSelectCandidate={setSelectedId}
      filter={filter}
      setFilter={setFilter}
    />
  </MainLayout>;
}

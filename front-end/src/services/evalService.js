export const handleEvaluate = async () => {
    try {
        setIsLoading(true);

        // Gọi API xét hồ sơ
        const response = await fetch("http://127.0.0.1:8000/api/evaluate", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Có lỗi xảy ra");
        }

        console.log(data);

    } catch (error) {
        console.error("Lỗi xét hồ sơ:", error);
    } finally {
        setIsLoading(false);
    }
};   

function handleEvaluate() {
    const payload = {
        lawFiles: lawFiles.map(file => file.name),
        candidates: candidates.map(candidate => candidate.id),
        criteria: criteria.map(criterion => criterion.id),
    };
    console.log("Xét hồ sơ - dữ liệu pipeline:", payload);
    setNotice("Đã gửi yêu cầu xét hồ sơ (API pipeline chưa được kết nối).");
}
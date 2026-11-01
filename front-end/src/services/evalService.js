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
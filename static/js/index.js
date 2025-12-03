function copy_to_clipboard(event) {
    const copyText = document.getElementById("manifest_url");
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(copyText.value)
            .then(() => {
                const btn = event.target.closest('button');
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<i class="bi bi-check"></i>';
                setTimeout(() => btn.innerHTML = originalHTML, 2000);
            })
            .catch(() => alert("Failed to copy"));
    } else {
        copyText.select();
        copyText.setSelectionRange(0, 99999);
        document.execCommand('copy');
    }
}

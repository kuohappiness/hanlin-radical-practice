const pendingDialog = document.querySelector("#pendingDialog");
const dialogTitle = document.querySelector("#dialogTitle");
const dialogClose = document.querySelector("#dialogClose");

document.querySelectorAll(".version-card").forEach((card) => {
  card.addEventListener("click", () => {
    const href = card.dataset.href;
    if (href) {
      window.location.href = href;
      return;
    }

    dialogTitle.textContent = card.dataset.version + "題庫尚未匯入";
    pendingDialog.showModal();
  });
});

dialogClose.addEventListener("click", () => pendingDialog.close());

pendingDialog.addEventListener("click", (event) => {
  if (event.target === pendingDialog) pendingDialog.close();
});

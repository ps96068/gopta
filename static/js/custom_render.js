Object.assign(
    render, {
      mycustomkey: function render(data, type, full, meta, fieldOptions) {
          console.log("in my custom render JS function");
          console.log(data);

          if (!data) return null_column();






    },
});
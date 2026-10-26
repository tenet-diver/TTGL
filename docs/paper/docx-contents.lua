-- Static linked contents survive headless rendering and remain usable in Word.
-- No page numbers are cached: pagination can change when the author edits.
function Pandoc(doc)
  local entries = pandoc.List()
  local chapter, section = 0, 0
  for _, block in ipairs(doc.blocks) do
    if block.t == 'Header' and block.level <= 2 then
      local numbered = not block.classes:includes('unnumbered')
      local prefix = ''
      if block.level == 1 and numbered then
        chapter, section = chapter + 1, 0
        prefix = tostring(chapter) .. '  '
      elseif block.level == 2 and numbered then
        section = section + 1
        prefix = tostring(chapter) .. '.' .. tostring(section) .. '  '
      end
      local label = prefix .. pandoc.utils.stringify(block.content)
      local item = pandoc.Para({pandoc.Link(label, '#' .. block.identifier)})
      entries:insert(pandoc.Div({item}, pandoc.Attr('', {},
        {['custom-style'] = block.level == 1 and 'TOC 1' or 'TOC 2'})))
    end
  end
  local pagebreak = pandoc.RawBlock('openxml',
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  local blocks = pandoc.List({pagebreak,
    pandoc.Header(1, 'Contents', pandoc.Attr('contents', {'unnumbered', 'unlisted'}))})
  blocks:extend(entries)
  blocks:insert(pagebreak)
  blocks:extend(doc.blocks)
  doc.blocks = blocks
  return doc
end

-- Permit long identifiers and paths to wrap without changing their content.
function Code(el)
  if FORMAT:match('latex') and #el.text >= 30 and not el.text:match('[{}]') then
    return pandoc.RawInline('latex', '\\nolinkurl{' .. el.text .. '}')
  end
end
